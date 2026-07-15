"""Apply Cloud Chamber CM1 source customizations outside the repo.

CM1 remains an external dependency. Differential surface forcing needs a small
source customization because the stock ``set_flx=1`` path writes uniform
``thflux``/``qvflux`` fields from namelist constants. This module copies the
configured external CM1 tree into an isolated runtime build tree, patches that
copy, rebuilds ``cm1.exe``, copies the exact customized executable into the run
directory, and records the operation beside the generated package.
"""

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

from cloud_chamber.run_manifest import RunManifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.surface_forcing import (
    CM1_SOURCE_CUSTOMIZATION_FILENAME,
    DIFFERENTIAL_SURFACE_FORCING_MODE,
    SURFACE_FORCING_PATCH_FILENAME,
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

SOURCE_CUSTOMIZATION_STATUS_FILENAME = "cm1_source_customization_applied.json"
SFCPHYS_MARKER = "CLOUD_CHAMBER_SURFACE_FORCING_PATCH_V0_SFCPHYS"

SFCPHYS_TARGET = Path("src/sfcphys.F")
CUSTOM_EXECUTABLE_FILENAME = "cm1_cloud_chamber_custom.exe"


class CM1SourceCustomizationError(RuntimeError):
    """Raised when differential surface forcing cannot customize local CM1."""


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
    return manifest.run_configuration.get("surface_flux_mode") == DIFFERENTIAL_SURFACE_FORCING_MODE


def prepare_cm1_source_customization(
    *,
    settings: CloudChamberSettings,
    manifest: RunManifest,
    command_runner: CommandRunner = subprocess.run,
) -> CM1SourceCustomizationResult | None:
    """Patch and rebuild the external CM1 tree for differential surface forcing."""

    if not manifest_requires_cm1_source_customization(manifest):
        return None

    if settings.cm1_root is None:
        raise CM1SourceCustomizationError(
            "Differential surface forcing requires a configured CM1 root with source files."
        )
    if settings.cm1_run_dir is None:
        raise CM1SourceCustomizationError(
            "Differential surface forcing requires a configured CM1 run directory."
        )

    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    patch_path = _required_generated_path(
        manifest.generated_inputs.surface_forcing_patch,
        run_dir / SURFACE_FORCING_PATCH_FILENAME,
        "surface forcing patch file",
    )
    customization_path = _required_generated_path(
        manifest.generated_inputs.cm1_source_customization,
        run_dir / CM1_SOURCE_CUSTOMIZATION_FILENAME,
        "CM1 source customization manifest",
    )
    _validate_patch_provenance(
        manifest=manifest,
        patch_path=patch_path,
        customization_path=customization_path,
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
        target = build_root / SFCPHYS_TARGET
        if not target.exists():
            raise CM1SourceCustomizationError(f"CM1 source file does not exist: {target}")
        target.write_text(_patch_sfcphys_text(target.read_text()))
        patched_files.append(str(SFCPHYS_TARGET))
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
                "Failed to rebuild CM1 after applying differential surface-forcing source "
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
    status_payload = {
        "schema_version": "cm1_source_customization_status_v0",
        "surface_flux_mode": DIFFERENTIAL_SURFACE_FORCING_MODE,
        "run_id": manifest.run_id,
        "applied_at": datetime.now(UTC).isoformat(),
        "cm1_root": str(settings.cm1_root),
        "cm1_run_dir": str(settings.cm1_run_dir),
        "source_hash": source_hash,
        "build_root": str(build_root),
        "patch_file": str(patch_path),
        "customization_manifest": str(customization_path),
        "patched_files": patched_files,
        "source_restored_after_build": "not_modified_isolated_build_tree",
        "build_command": ["make"],
        "custom_executable": str(executable_path),
        "custom_executable_sha256": executable_sha256,
        "no_silent_uniform_fallback": True,
    }
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


def _fail_if_source_already_customized(cm1_root: Path) -> None:
    dirty_files = []
    for relative_path in (SFCPHYS_TARGET,):
        path = cm1_root / relative_path
        if path.exists() and SFCPHYS_MARKER in path.read_text(errors="replace"):
            dirty_files.append(str(relative_path))
    if dirty_files:
        raise CM1SourceCustomizationError(
            "Configured CM1 source tree already contains Cloud Chamber differential "
            "surface-forcing customization markers. Refusing to build from a dirty "
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
            "Differential surface forcing currently requires cm1_run_dir to live under cm1_root "
            "so the isolated build tree can identify the generated executable."
        ) from exc
    return build_root / relative_run_dir / "cm1.exe"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


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
    "manifest_requires_cm1_source_customization",
    "prepare_cm1_source_customization",
]
