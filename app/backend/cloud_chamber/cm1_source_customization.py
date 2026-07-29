"""Apply source-locked Cloud Chamber CM1 customizations outside the repo."""

from __future__ import annotations

import fcntl
import hashlib
import json
import shutil
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from cloud_chamber.run_manifest import RunManifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercell_hodograph import (
    STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
    STRAIGHT_LINE_HODOGRAPH_MARKER,
    STRAIGHT_LINE_HODOGRAPH_SCHEMA_VERSION,
    STRAIGHT_LINE_HODOGRAPH_TARGET,
    StraightLineHodographError,
    render_straight_line_hodograph_source,
)
from cloud_chamber.supercells_source_customization import (
    SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
    SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET,
    SupercellsSourceCustomizationError,
    load_supercells_source_customization,
    render_supercells_source,
)
from cloud_chamber.surface_forcing import (
    CM1_SOURCE_CUSTOMIZATION_FILENAME,
    DIFFERENTIAL_SURFACE_FORCING_MODE,
    SURFACE_FORCING_PATCH_FILENAME,
)
from cloud_chamber.trade_cumulus_forcing import (
    TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
    TRADE_CUMULUS_FORCING_MARKER,
    TRADE_CUMULUS_FORCING_TARGET,
    TradeCumulusForcingError,
    load_forcing_customization,
    render_trade_cumulus_forcing_source,
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

SOURCE_CUSTOMIZATION_STATUS_FILENAME = "cm1_source_customization_applied.json"
SURFACE_FORCING_CUSTOMIZATION_KIND = "differential_surface_forcing_v0"
SFCPHYS_MARKER = "CLOUD_CHAMBER_SURFACE_FORCING_PATCH_V0_SFCPHYS"

SFCPHYS_TARGET = Path("src/sfcphys.F")
CUSTOM_EXECUTABLE_FILENAME = "cm1_cloud_chamber_custom.exe"


class CM1SourceCustomizationError(RuntimeError):
    """Raised when a declared source customization cannot rebuild local CM1."""


@dataclass(frozen=True)
class CM1SourceCustomizationResult:
    status_path: Path
    build_root: Path
    executable_path: Path
    source_hash: str
    executable_sha256: str
    patched_files: tuple[str, ...]
    build_command: tuple[str, ...]


def manifest_requires_cm1_source_customization(manifest: RunManifest) -> bool:
    return (
        manifest.run_configuration.get("surface_flux_mode") == DIFFERENTIAL_SURFACE_FORCING_MODE
        or manifest.run_configuration.get("cm1_source_customization_kind") is not None
    )


def prepare_cm1_source_customization(
    *,
    settings: CloudChamberSettings,
    manifest: RunManifest,
    command_runner: CommandRunner = subprocess.run,
) -> CM1SourceCustomizationResult | None:
    """Patch and rebuild an isolated copy of the configured external CM1 tree."""

    if not manifest_requires_cm1_source_customization(manifest):
        return None

    customization_kind = _customization_kind(manifest)
    if settings.cm1_root is None:
        raise CM1SourceCustomizationError(
            "CM1 source customization requires a configured CM1 root with source files."
        )
    if settings.cm1_run_dir is None:
        raise CM1SourceCustomizationError(
            "CM1 source customization requires a configured CM1 run directory."
        )

    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    customization_path = _required_generated_path(
        manifest.generated_inputs.cm1_source_customization,
        run_dir / CM1_SOURCE_CUSTOMIZATION_FILENAME,
        "CM1 source customization manifest",
    )
    if customization_kind == SURFACE_FORCING_CUSTOMIZATION_KIND:
        patch_path = _required_generated_path(
            manifest.generated_inputs.surface_forcing_patch,
            run_dir / SURFACE_FORCING_PATCH_FILENAME,
            "surface forcing patch file",
        )
        _validate_patch_provenance(
            manifest=manifest,
            patch_path=patch_path,
            customization_path=customization_path,
        )
        target_relative_path = SFCPHYS_TARGET
        patch_source = _patch_sfcphys_text
        expected_original_sha256 = None
        expected_patched_sha256 = None
        status_details: dict[str, object] = {
            "surface_flux_mode": DIFFERENTIAL_SURFACE_FORCING_MODE,
            "patch_file": str(patch_path),
            "no_silent_uniform_fallback": True,
        }
    elif customization_kind == STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND:
        customization = _validate_straight_line_hodograph_provenance(
            manifest=manifest,
            customization_path=customization_path,
        )
        target_relative_path = STRAIGHT_LINE_HODOGRAPH_TARGET
        patch_source = render_straight_line_hodograph_source
        expected_original_sha256 = str(customization["original_source_sha256"])
        expected_patched_sha256 = str(customization["patched_source_sha256"])
        status_details = {
            "hodograph_profile": customization["wind_profile"],
            "no_silent_hodograph_fallback": True,
        }
    elif customization_kind == TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND:
        customization = load_forcing_customization(customization_path)
        target_relative_path = TRADE_CUMULUS_FORCING_TARGET
        forcing = cast(dict[str, Any], customization["forcing"])

        def patch_source(source: str) -> str:
            return render_trade_cumulus_forcing_source(source, forcing)

        expected_original_sha256 = str(customization["original_source_sha256"])
        expected_patched_sha256 = str(customization["patched_source_sha256"])
        status_details = {
            "forcing": customization["forcing"],
            "no_silent_forcing_fallback": True,
        }
    elif customization_kind == SUPERCELLS_SOURCE_CUSTOMIZATION_KIND:
        customization = load_supercells_source_customization(customization_path)
        target_relative_path = SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET
        initiation = cast(dict[str, float], customization["initiation"])

        def patch_source(source: str) -> str:
            return render_supercells_source(source, initiation)

        expected_original_sha256 = str(customization["original_source_sha256"])
        expected_patched_sha256 = str(customization["patched_source_sha256"])
        status_details = {
            "initiation": initiation,
            "wind_profile_sha256": customization["wind_profile_sha256"],
            "thermodynamic_profile_sha256": customization["thermodynamic_profile_sha256"],
            "no_silent_profile_or_thermal_fallback": True,
        }
    else:
        raise CM1SourceCustomizationError(
            f"Unsupported CM1 source customization kind: {customization_kind}"
        )

    src_dir = settings.cm1_root / "src"
    if not src_dir.exists():
        raise CM1SourceCustomizationError(f"CM1 source directory does not exist: {src_dir}")
    makefile = src_dir / "Makefile"
    if not makefile.exists():
        raise CM1SourceCustomizationError(f"CM1 Makefile does not exist: {makefile}")

    _fail_if_source_already_customized(settings.cm1_root)
    source_hash = _source_tree_hash(src_dir)
    build_root = (
        settings.runtime_home / "cm1_source_builds" / f"{source_hash[:16]}-{manifest.run_id}"
    )
    patched_files: list[str] = []
    with _cm1_build_lock(settings.runtime_home):
        if build_root.exists():
            shutil.rmtree(build_root)
        shutil.copytree(settings.cm1_root, build_root, ignore=_copytree_ignore)
        build_src_dir = build_root / "src"
        target = build_root / target_relative_path
        if not target.exists():
            raise CM1SourceCustomizationError(f"CM1 source file does not exist: {target}")
        original_source = target.read_text()
        original_source_sha256 = _text_sha256(original_source)
        if (
            expected_original_sha256 is not None
            and original_source_sha256 != expected_original_sha256
        ):
            raise CM1SourceCustomizationError(
                "Configured CM1 source target does not match the packaged source lock: "
                f"{original_source_sha256} != {expected_original_sha256}."
            )
        try:
            patched_source = patch_source(original_source)
        except (
            StraightLineHodographError,
            SupercellsSourceCustomizationError,
            TradeCumulusForcingError,
        ) as exc:
            raise CM1SourceCustomizationError(str(exc)) from exc
        patched_source_sha256 = _text_sha256(patched_source)
        if expected_patched_sha256 is not None and patched_source_sha256 != expected_patched_sha256:
            raise CM1SourceCustomizationError(
                "Rendered CM1 source target does not match the packaged customization identity."
            )
        target.write_text(patched_source)
        patched_files.append(str(target_relative_path))
        build_command = ("make",)
        try:
            command_runner(
                list(build_command),
                cwd=build_src_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise CM1SourceCustomizationError(
                "Failed to rebuild CM1 after applying the declared source "
                f"customization in isolated build tree: {exc.stderr or exc.stdout or exc}"
            ) from exc

    built_executable = _built_executable_path(
        original_cm1_root=settings.cm1_root,
        original_cm1_run_dir=settings.cm1_run_dir,
        build_root=build_root,
    )
    if not built_executable.exists():
        raise CM1SourceCustomizationError(
            "CM1 rebuild did not produce an executable in the isolated build tree: "
            f"{built_executable}"
        )
    executable_path = run_dir / CUSTOM_EXECUTABLE_FILENAME
    shutil.copy2(built_executable, executable_path)
    executable_sha256 = _file_sha256(executable_path)

    status_path = run_dir / SOURCE_CUSTOMIZATION_STATUS_FILENAME
    status_payload: dict[str, object] = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": customization_kind,
        "run_id": manifest.run_id,
        "applied_at": datetime.now(UTC).isoformat(),
        "cm1_root": str(settings.cm1_root),
        "cm1_run_dir": str(settings.cm1_run_dir),
        "source_hash": source_hash,
        "build_root": str(build_root),
        "customization_manifest": str(customization_path),
        "original_target_sha256": original_source_sha256,
        "patched_target_sha256": patched_source_sha256,
        "patched_files": patched_files,
        "source_restored_after_build": "not_modified_isolated_build_tree",
        "build_command": ["make"],
        "custom_executable": str(executable_path),
        "custom_executable_sha256": executable_sha256,
    }
    status_payload.update(status_details)
    status_path.write_text(json.dumps(status_payload, indent=2, sort_keys=True) + "\n")
    return CM1SourceCustomizationResult(
        status_path=status_path,
        build_root=build_root,
        executable_path=executable_path,
        source_hash=source_hash,
        executable_sha256=executable_sha256,
        patched_files=tuple(patched_files),
        build_command=("make",),
    )


def _customization_kind(manifest: RunManifest) -> str:
    if manifest.run_configuration.get("surface_flux_mode") == DIFFERENTIAL_SURFACE_FORCING_MODE:
        return SURFACE_FORCING_CUSTOMIZATION_KIND
    kind = manifest.run_configuration.get("cm1_source_customization_kind")
    if not isinstance(kind, str) or not kind:
        raise CM1SourceCustomizationError(
            "Run manifest declares source customization without a valid customization kind."
        )
    return kind


def _required_generated_path(value: str | None, fallback: Path, label: str) -> Path:
    path = Path(value).expanduser() if value else fallback
    if not path.exists():
        raise CM1SourceCustomizationError(f"Missing generated {label}: {path}")
    return path


def _validate_patch_provenance(
    *,
    manifest: RunManifest,
    patch_path: Path,
    customization_path: Path,
) -> None:
    if not patch_path.exists():
        raise CM1SourceCustomizationError(f"Missing generated {patch_path.name}: {patch_path}")
    if not customization_path.exists():
        raise CM1SourceCustomizationError(
            f"Missing generated {customization_path.name}: {customization_path}"
        )
    try:
        customization = json.loads(customization_path.read_text())
    except json.JSONDecodeError as exc:
        raise CM1SourceCustomizationError(
            f"Generated CM1 source-customization manifest is invalid JSON: {customization_path}"
        ) from exc
    patch = manifest.run_configuration.get("surface_forcing_patch")
    if not isinstance(patch, dict):
        raise CM1SourceCustomizationError(
            "Differential run manifest is missing surface_forcing_patch provenance."
        )
    expected_pattern_hash = patch.get("pattern_sha256")
    if not isinstance(expected_pattern_hash, str) or not expected_pattern_hash:
        raise CM1SourceCustomizationError(
            "Differential run manifest is missing surface_forcing_patch.pattern_sha256."
        )
    if customization.get("surface_patch_sha256") != expected_pattern_hash:
        raise CM1SourceCustomizationError(
            "CM1 source-customization manifest does not match the run manifest patch hash."
        )
    expected_data_hash = customization.get("runtime_patch_file_sha256")
    if not isinstance(expected_data_hash, str) or not expected_data_hash:
        raise CM1SourceCustomizationError(
            "CM1 source-customization manifest is missing runtime_patch_file_sha256."
        )
    actual_data_hash = _file_sha256(patch_path)
    if actual_data_hash != expected_data_hash:
        raise CM1SourceCustomizationError(
            "Generated surface-forcing patch data does not match the source-customization "
            f"manifest hash: expected {expected_data_hash}, got {actual_data_hash}."
        )


def _validate_straight_line_hodograph_provenance(
    *,
    manifest: RunManifest,
    customization_path: Path,
) -> dict[str, object]:
    try:
        customization = json.loads(customization_path.read_text())
    except json.JSONDecodeError as exc:
        raise CM1SourceCustomizationError(
            f"Generated straight-line hodograph customization is invalid JSON: {customization_path}"
        ) from exc
    if not isinstance(customization, dict):
        raise CM1SourceCustomizationError(
            "Generated straight-line hodograph customization is not an object."
        )
    expected = {
        "schema_version": STRAIGHT_LINE_HODOGRAPH_SCHEMA_VERSION,
        "customization_kind": STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
        "target_relative_path": str(STRAIGHT_LINE_HODOGRAPH_TARGET),
        "marker": STRAIGHT_LINE_HODOGRAPH_MARKER,
    }
    mismatched = {
        name: (customization.get(name), value)
        for name, value in expected.items()
        if customization.get(name) != value
    }
    if mismatched:
        raise CM1SourceCustomizationError(
            f"Straight-line hodograph customization identity changed: {mismatched}."
        )
    if (
        manifest.run_configuration.get("cm1_source_customization_kind")
        != STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND
    ):
        raise CM1SourceCustomizationError(
            "Run manifest and generated straight-line hodograph customization disagree."
        )
    for name in ("original_source_sha256", "patched_source_sha256"):
        value = customization.get(name)
        if not isinstance(value, str) or len(value) != 64:
            raise CM1SourceCustomizationError(
                f"Straight-line hodograph customization is missing {name}."
            )
    wind_profile = customization.get("wind_profile")
    if not isinstance(wind_profile, dict):
        raise CM1SourceCustomizationError(
            "Straight-line hodograph customization is missing its wind profile."
        )
    return customization


def _fail_if_source_already_customized(cm1_root: Path) -> None:
    dirty_files = []
    targets = (
        (SFCPHYS_TARGET, SFCPHYS_MARKER),
        (STRAIGHT_LINE_HODOGRAPH_TARGET, STRAIGHT_LINE_HODOGRAPH_MARKER),
        (TRADE_CUMULUS_FORCING_TARGET, TRADE_CUMULUS_FORCING_MARKER),
    )
    for relative_path, marker in targets:
        path = cm1_root / relative_path
        if path.exists() and marker in path.read_text(errors="replace"):
            dirty_files.append(str(relative_path))
    if dirty_files:
        raise CM1SourceCustomizationError(
            "Configured CM1 source tree already contains Cloud Chamber customization "
            "markers. Refusing to build from a dirty "
            "source tree: " + ", ".join(dirty_files)
        )


@contextmanager
def _cm1_build_lock(runtime_home: Path) -> Iterator[None]:
    lock_dir = runtime_home / "cm1_source_builds"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".cm1-build.lock"
    with lock_path.open("w") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _copytree_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {".git", "__pycache__", ".DS_Store"}
    ignored.update(
        name for name in names if name.startswith("cm1out_") or name in {"logs", "LOG", "output"}
    )
    return ignored


def _source_tree_hash(src_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in src_dir.rglob("*") if candidate.is_file()):
        relative = path.relative_to(src_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _built_executable_path(
    *,
    original_cm1_root: Path,
    original_cm1_run_dir: Path,
    build_root: Path,
) -> Path:
    try:
        relative_run_dir = original_cm1_run_dir.relative_to(original_cm1_root)
    except ValueError as exc:
        raise CM1SourceCustomizationError(
            "CM1 source customization requires cm1_run_dir to live under cm1_root "
            "so the isolated build tree can identify the generated executable."
        ) from exc
    return build_root / relative_run_dir / "cm1.exe"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _patch_sfcphys_text(source: str) -> str:
    if SFCPHYS_MARKER in source:
        return source
    declarations_anchor = "      real :: thmag,qvmag,trat1,trat2\n"
    declarations_replacement = """      real :: thmag,qvmag,trat1,trat2
      logical, save :: cc_patch_loaded = .false.
      logical, save :: cc_patch_enabled = .false.
      real, save :: cc_patch_bg_h = 0.0
      real, save :: cc_patch_bg_q = 0.0
      real, save :: cc_patch_dh = 0.0
      real, save :: cc_patch_dq = 0.0
      real, save :: cc_patch_cx = 0.0
      real, save :: cc_patch_cy = 0.0
      real, save :: cc_patch_rx = 0.0
      real, save :: cc_patch_ry = 0.0
      real, save :: cc_patch_taper = 0.0
      real, save :: cc_patch_ramp = 0.0
      integer :: cc_unit,cc_ios
      real :: cc_x,cc_y,cc_r,cc_weight,cc_taper_norm,cc_ramp
      character(len=256) :: cc_header
"""
    if declarations_anchor not in source:
        raise CM1SourceCustomizationError(
            "Unable to locate sfcphys.F declaration anchor for differential forcing."
        )
    source = source.replace(declarations_anchor, declarations_replacement, 1)

    flux_anchor = """    ENDIF

  !c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c!

  ELSE
"""
    flux_replacement = f"""    ENDIF

    ! {SFCPHYS_MARKER}
    if( .not. cc_patch_loaded )then
      inquire(file='{SURFACE_FORCING_PATCH_FILENAME}',exist=cc_patch_enabled)
      if( .not. cc_patch_enabled )then
        write(0,*) 'Cloud Chamber differential surface-forcing patch file is missing.'
        stop 811
      endif
      cc_unit = 981
      open(unit=cc_unit,file='{SURFACE_FORCING_PATCH_FILENAME}',status='old',action='read',iostat=cc_ios)
      if( cc_ios.ne.0 )then
        write(0,*) 'Cloud Chamber could not open differential surface-forcing patch file.'
        stop 812
      endif
      read(cc_unit,'(A)',iostat=cc_ios) cc_header
      if( cc_ios.ne.0 )then
        write(0,*) 'Cloud Chamber differential surface-forcing patch header is malformed.'
        close(cc_unit)
        stop 813
      endif
      read(cc_unit,'(A)',iostat=cc_ios) cc_header
      if( cc_ios.ne.0 )then
        write(0,*) 'Cloud Chamber differential surface-forcing patch column header is malformed.'
        close(cc_unit)
        stop 814
      endif
      read(cc_unit,*,iostat=cc_ios) cc_patch_bg_h,cc_patch_bg_q,cc_patch_dh,cc_patch_dq,  &
                                  cc_patch_cx,cc_patch_cy,cc_patch_rx,cc_patch_ry,      &
                                  cc_patch_taper,cc_patch_ramp
      close(cc_unit)
      if( cc_ios.ne.0 )then
        write(0,*) 'Cloud Chamber differential surface-forcing patch values are malformed.'
        stop 815
      endif
      cc_patch_loaded = .true.
    endif

    if( cc_patch_enabled )then
      cc_taper_norm = max( cc_patch_taper/min(cc_patch_rx,cc_patch_ry) , 1.0e-6 )
      cc_ramp = min( max( rtime/max(cc_patch_ramp,1.0e-6) , 0.0 ) , 1.0 )
      !$omp parallel do default(shared)   &
      !$omp private(i,j,cc_x,cc_y,cc_r,cc_weight)
      DO j=1,nj
      do i=1,ni
        cc_x = minx + (float(i)-0.5)*dx - centerx - cc_patch_cx
        cc_y = miny + (float(j)-0.5)*dy - centery - cc_patch_cy
        cc_r = sqrt( (cc_x/cc_patch_rx)**2 + (cc_y/cc_patch_ry)**2 )
        if( cc_r.le.1.0 )then
          cc_weight = 1.0
        elseif( cc_r.lt.(1.0+cc_taper_norm) )then
          cc_weight = 0.5*( 1.0 + cos( pi*(cc_r-1.0)/cc_taper_norm ) )
        else
          cc_weight = 0.0
        endif
        thflux(i,j) = cc_patch_bg_h + cc_patch_dh*cc_weight*cc_ramp
        if( imoist.eq.1 ) qvflux(i,j) = cc_patch_bg_q + cc_patch_dq*cc_weight*cc_ramp
      enddo
      ENDDO
    endif

  !c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c-c!

  ELSE
"""
    if flux_anchor not in source:
        raise CM1SourceCustomizationError(
            "Unable to locate sfcphys.F set_flx branch for differential forcing."
        )
    return source.replace(flux_anchor, flux_replacement, 1)


__all__ = [
    "CM1SourceCustomizationError",
    "CM1SourceCustomizationResult",
    "CUSTOM_EXECUTABLE_FILENAME",
    "SOURCE_CUSTOMIZATION_STATUS_FILENAME",
    "SURFACE_FORCING_CUSTOMIZATION_KIND",
    "manifest_requires_cm1_source_customization",
    "prepare_cm1_source_customization",
]
