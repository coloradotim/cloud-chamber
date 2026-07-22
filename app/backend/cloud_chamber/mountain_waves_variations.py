"""Deterministic parent-based Mountain Waves variation packaging."""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator

from cloud_chamber import __version__
from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.mountain_wave_case import (
    collect_cm1_provenance,
    parse_namelist_assignments,
    replace_namelist_assignment,
    sha256_file,
    verified_clean_git_commit,
)
from cloud_chamber.mountain_wave_terrain_visualization import (
    MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS,
)
from cloud_chamber.mountain_waves_world import (
    MOIST_SIMULATION_ID,
    WORLD_ID,
    MountainWavesSimulationRecord,
    mountain_waves_run_manifest,
)
from cloud_chamber.run_manifest import (
    AppMetadata,
    GeneratedInputs,
    LifecycleState,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    RuntimePaths,
    ScenarioReference,
    UserMetadata,
    ValidationStatus,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

VARIATION_CASE_ID = "mountain_waves_exploratory_variation_v1"
VARIATION_SCHEMA_VERSION = "mountain_waves_variation_v1"
DIFFERENCE_GROUPS = (
    "terrain",
    "wind",
    "moisture",
    "stability/thermodynamics",
    "numerics/time",
    "output",
)


class MountainWavesVariationError(RuntimeError):
    """Raised when an exploratory variation cannot be represented or packaged honestly."""


class TerrainConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_m: float
    half_width_m: float
    center_m: float


class SoundingLevel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_m: float
    pressure_pa: float
    theta_k: float
    qv_g_kg: float
    u_m_s: float
    v_m_s: float = 0.0


class MountainWavesConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terrain: TerrainConfiguration
    sounding: list[SoundingLevel]
    duration_seconds: int
    output_cadence_seconds: int

    @model_validator(mode="after")
    def validate_shape(self) -> MountainWavesConfiguration:
        if len(self.sounding) < 3:
            raise ValueError("A Mountain Waves sounding needs at least three levels.")
        heights = [level.height_m for level in self.sounding]
        if heights[0] != 0.0 or any(
            right <= left for left, right in zip(heights, heights[1:], strict=False)
        ):
            raise ValueError("Sounding heights must begin at 0 m and increase strictly.")
        if any(level.v_m_s != 0.0 for level in self.sounding):
            raise ValueError(
                "The first Mountain Waves implementation preserves two-dimensional v=0 flow."
            )
        return self


class MountainWavesVariationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str = MOIST_SIMULATION_ID
    simulation_name: str
    user_question: str | None = None
    configuration: MountainWavesConfiguration


class MountainWavesVariationTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str
    parent_run_id: str
    parent_display_name: str
    parent_configuration_source: str
    reference_simulation_id: str = MOIST_SIMULATION_ID
    configuration: MountainWavesConfiguration
    can_create_variation: bool
    unavailable_reason: str | None = None


class MountainWavesVariationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    differences: dict[str, list[dict[str, Any]]]
    warnings: list[str]
    blocking_errors: list[str]
    derived_stability_n2_s2: list[float]
    terrain_profile: list[dict[str, float]]


class MountainWavesVariationPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    run_id: str
    manifest_path: str
    package_dir: str
    differences: dict[str, list[dict[str, Any]]]
    warnings: list[str]
    preflight: dict[str, Any]


def mountain_waves_variation_template(
    settings: CloudChamberSettings, parent_simulation_id: str
) -> MountainWavesVariationTemplate:
    template, _parent, _manifest, _manifest_path = _variation_template_context(
        settings, parent_simulation_id
    )
    return template


def _variation_template_context(
    settings: CloudChamberSettings, parent_simulation_id: str
) -> tuple[MountainWavesVariationTemplate, MountainWavesSimulationRecord, RunManifest, Path]:
    parent, manifest, manifest_path = mountain_waves_run_manifest(settings, parent_simulation_id)
    if not parent.can_create_variation:
        unavailable_reason = (
            "Dry Ridge preserves a source-defined analytic atmosphere and terrain setup "
            "that this variation package cannot inherit exactly; it remains inspectable "
            "but is not an editable parent."
            if not parent.moist_fields_available
            else "This Simulation does not retain an exact editable configuration."
        )
        return (
            MountainWavesVariationTemplate(
                parent_simulation_id=parent.simulation_id,
                parent_run_id=parent.run_id,
                parent_display_name=parent.display_name,
                parent_configuration_source="unavailable",
                configuration=_fallback_configuration(parent, manifest),
                can_create_variation=False,
                unavailable_reason=unavailable_reason,
            ),
            parent,
            manifest,
            manifest_path,
        )
    configuration = _configuration_from_parent(parent, manifest, manifest_path)
    return (
        MountainWavesVariationTemplate(
            parent_simulation_id=parent.simulation_id,
            parent_run_id=parent.run_id,
            parent_display_name=parent.display_name,
            parent_configuration_source=_parent_configuration_source(parent),
            configuration=configuration,
            can_create_variation=True,
        ),
        parent,
        manifest,
        manifest_path,
    )


def preview_mountain_waves_variation(
    settings: CloudChamberSettings, request: MountainWavesVariationRequest
) -> MountainWavesVariationPreview:
    template, _parent, parent_manifest, _manifest_path = _variation_template_context(
        settings, request.parent_simulation_id
    )
    return _preview_mountain_waves_variation(request, template, parent_manifest)


def _preview_mountain_waves_variation(
    request: MountainWavesVariationRequest,
    template: MountainWavesVariationTemplate,
    parent_manifest: RunManifest,
) -> MountainWavesVariationPreview:
    if not template.can_create_variation:
        return MountainWavesVariationPreview(
            differences=_empty_differences(),
            warnings=[],
            blocking_errors=[template.unavailable_reason or "The selected parent is unavailable."],
            derived_stability_n2_s2=[],
            terrain_profile=[],
        )
    differences = configuration_differences(template.configuration, request.configuration)
    blocking = _configuration_errors(
        request,
        parent=template.configuration,
        inherited_domain=parent_manifest.run_configuration.get("domain"),
        required_top_m=template.configuration.sounding[-1].height_m,
    )
    if not any(differences.values()):
        blocking.append(
            "Change at least one editable setting; an unchanged technical rerun is a "
            "separate action."
        )
    warnings = configuration_warnings(request.configuration, differences)
    return MountainWavesVariationPreview(
        differences=differences,
        warnings=warnings,
        blocking_errors=blocking,
        derived_stability_n2_s2=_stability_profile(request.configuration.sounding),
        terrain_profile=_terrain_preview(request.configuration, points=121),
    )


def create_mountain_waves_variation(
    settings: CloudChamberSettings, request: MountainWavesVariationRequest
) -> MountainWavesVariationPackage:
    template, parent, parent_manifest, parent_manifest_path = _variation_template_context(
        settings, request.parent_simulation_id
    )
    preview = _preview_mountain_waves_variation(request, template, parent_manifest)
    if preview.blocking_errors:
        raise MountainWavesVariationError(" ".join(preview.blocking_errors))
    if not template.can_create_variation:
        raise MountainWavesVariationError(template.unavailable_reason or "Parent is unavailable.")

    implementation_commit = verified_clean_git_commit()
    provenance = collect_cm1_provenance(settings)
    identity_suffix = uuid4().hex[:8]
    slug = _slug(request.simulation_name)
    simulation_id = f"mountain_waves_{slug}_{identity_suffix}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"mw-{slug}-{timestamp}-{identity_suffix[:4]}"
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise MountainWavesVariationError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)

    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "sounding": package_dir / "input_sounding",
        "terrain": package_dir / "perts.dat",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "package_report": package_dir / "mountain_waves_variation.json",
    }
    try:
        parent_run_dir = Path(parent_manifest.generated_inputs.run_directory).expanduser()
        parent_namelist = parent_run_dir / "namelist.input"
        if not parent_namelist.is_file():
            raise MountainWavesVariationError("The parent namelist is unavailable.")
        namelist = _render_variation_namelist(parent_namelist.read_text(), request.configuration)
        paths["namelist"].write_text(namelist)
        paths["sounding"].write_text(_render_input_sounding(request.configuration.sounding))
        terrain_audit = _write_terrain_file(paths["terrain"], namelist, request.configuration)
        runtime_checklist = {
            "status": "exact_variation_inputs_present",
            "consumed_files": ["input_sounding", "perts.dat"],
            "required_files": [],
            "source_candidates": {},
        }
        _write_json(paths["runtime_checklist"], runtime_checklist)
        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key not in {"manifest", "case_manifest", "package_report"}
        }
        now = datetime.now(UTC)
        configuration_payload = request.configuration.model_dump(mode="json")
        run_configuration: dict[str, Any] = {
            "cloud_world_id": WORLD_ID,
            "simulation_id": simulation_id,
            "simulation_display_name": request.simulation_name.strip(),
            "parent_simulation_id": parent.simulation_id,
            "parent_run_id": parent.run_id,
            "parent_configuration_source": template.parent_configuration_source,
            "reference_simulation_id": MOIST_SIMULATION_ID,
            "user_question": _optional_text(request.user_question),
            "mountain_waves_configuration": configuration_payload,
            "configuration_difference": preview.differences,
            "warnings": preview.warnings,
            "duration_seconds": request.configuration.duration_seconds,
            "output_cadence_seconds": request.configuration.output_cadence_seconds,
            "expected_model_output_count": (
                request.configuration.duration_seconds
                // request.configuration.output_cadence_seconds
                + 1
            ),
            "domain": _domain_record(namelist),
            "terrain": request.configuration.terrain.model_dump(mode="json"),
            "terrain_audit": terrain_audit,
            "generated_input_sha256": generated_hashes,
            "parent_manifest_path": str(parent_manifest_path),
            "cm1_provenance": provenance.report_record(),
        }
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(
                id=VARIATION_CASE_ID, schema_version=VARIATION_SCHEMA_VERSION
            ),
            controls={
                "terrain_height_m": request.configuration.terrain.height_m,
                "terrain_half_width_m": request.configuration.terrain.half_width_m,
                "terrain_center_m": request.configuration.terrain.center_m,
                "duration_seconds": request.configuration.duration_seconds,
                "output_cadence_seconds": request.configuration.output_cadence_seconds,
            },
            run_configuration=run_configuration,
            physical_question=(
                _optional_text(request.user_question)
                or (
                    f"What happens when {request.simulation_name.strip()} changes "
                    "the parent atmosphere and terrain?"
                )
            ),
            expected_diagnostics=[
                "terrain_following_wave_structure",
                "vertical_velocity_and_temperature_response",
                "cloud_condensate_relative_humidity_and_evaporation_when_present",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(package_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=str(paths["sounding"]),
                dry_run_report=str(paths["package_report"]),
                runtime_file_checklist=[str(paths["runtime_checklist"])],
            ),
            runtime_paths=RuntimePaths(
                runtime_home=str(settings.runtime_home.expanduser()),
                cm1_root=str(settings.cm1_root) if settings.cm1_root else None,
                cm1_run_dir=str(settings.cm1_run_dir) if settings.cm1_run_dir else None,
                cache_dir=str(settings.cache_dir),
                log_dir=str(settings.log_dir),
            ),
            app=AppMetadata(app_version=__version__, commit=implementation_commit),
            lifecycle_state=LifecycleState.PACKAGED,
            validation_status=ValidationStatus.NEEDS_REVIEW,
            provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
            created_at=now,
            updated_at=now,
            user=UserMetadata(
                name=request.simulation_name.strip(), notes=_optional_text(request.user_question)
            ),
            pre_run_validation_report={
                "status": "caveated",
                "blocking_errors": [],
                "caveats": preview.warnings,
                "configuration_difference": preview.differences,
                "package_path": "existing_local_run_manager",
            },
            required_output_fields=sorted(MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS),
            input_source="mountain_waves_parent_external_sounding_and_terrain",
            expected_outputs=["native_numbered_cm1_model_netcdf", "cm1_stats_and_logs"],
            run_caveats=preview.warnings,
            manual_validation_status="exploratory_user_variation",
        )
        write_run_manifest(paths["manifest"], manifest)
        case_manifest = {
            "schema_version": VARIATION_SCHEMA_VERSION,
            "cloud_world_id": WORLD_ID,
            "simulation_id": simulation_id,
            "simulation_display_name": request.simulation_name.strip(),
            "run_id": run_id,
            "implementation_commit": implementation_commit,
            "parent_simulation_id": parent.simulation_id,
            "parent_run_id": parent.run_id,
            "parent_configuration_source": template.parent_configuration_source,
            "reference_simulation_id": MOIST_SIMULATION_ID,
            "exact_configuration": configuration_payload,
            "configuration_difference": preview.differences,
            "warnings": preview.warnings,
            "generated_input_sha256": generated_hashes,
            "terrain_audit": terrain_audit,
            "cm1_provenance": provenance.report_record(),
        }
        _write_json(paths["case_manifest"], case_manifest)
        _write_json(
            paths["package_report"],
            {
                "status": "packaged_for_existing_local_run_manager",
                **case_manifest,
            },
        )
        preflight = preflight_mountain_waves_variation(paths["manifest"])
        return MountainWavesVariationPackage(
            simulation_id=simulation_id,
            run_id=run_id,
            manifest_path=str(paths["manifest"]),
            package_dir=str(package_dir),
            differences=preview.differences,
            warnings=preview.warnings,
            preflight=preflight,
        )
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise


def preflight_mountain_waves_variation(manifest_path: Path) -> dict[str, Any]:
    manifest = load_run_manifest(manifest_path.expanduser())
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise MountainWavesVariationError("Variation preflight requires a packaged manifest.")
    if manifest.run_configuration.get("cloud_world_id") != WORLD_ID:
        raise MountainWavesVariationError("Variation manifest does not belong to Mountain Waves.")
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    required = [
        run_dir / "namelist.input",
        run_dir / "input_sounding",
        run_dir / "perts.dat",
        run_dir / "runtime_file_checklist.json",
        run_dir / "case_manifest.json",
    ]
    missing = [path.name for path in required if not path.is_file()]
    outputs = sorted(path.name for path in run_dir.glob("cm1out*") if path.is_file())
    try:
        verified_hashes = verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError:
        verified_hashes = {}
    hash_checks = {name: True for name in verified_hashes}
    checks = {
        "packaged_manifest": True,
        "required_inputs_present": not missing,
        "generated_hashes_match": bool(hash_checks) and all(hash_checks.values()),
        "no_existing_cm1_output": not outputs,
        "two_dimensional_v_zero": _configuration_v_is_zero(manifest.run_configuration),
    }
    if not all(checks.values()):
        raise MountainWavesVariationError(
            "Variation package preflight failed: "
            f"checks={checks}, missing={missing}, outputs={outputs}"
        )
    return {
        "passed": True,
        "checks": checks,
        "missing": missing,
        "existing_outputs": outputs,
        "generated_hash_checks": hash_checks,
    }


def configuration_differences(
    parent: MountainWavesConfiguration, intended: MountainWavesConfiguration
) -> dict[str, list[dict[str, Any]]]:
    differences = _empty_differences()
    for field_name, label, units in (
        ("height_m", "Ridge height", "m"),
        ("half_width_m", "Ridge half-width", "m"),
        ("center_m", "Ridge center", "m"),
    ):
        before = getattr(parent.terrain, field_name)
        after = getattr(intended.terrain, field_name)
        if not math.isclose(before, after):
            differences["terrain"].append(_difference(label, before, after, units))
    paired_levels = zip(parent.sounding, intended.sounding, strict=False)
    for index, (before, after) in enumerate(paired_levels):
        level_label = f"{after.height_m:g} m"
        if not math.isclose(before.u_m_s, after.u_m_s):
            differences["wind"].append(
                _difference(f"u at {level_label}", before.u_m_s, after.u_m_s, "m/s", index)
            )
        if not math.isclose(before.qv_g_kg, after.qv_g_kg):
            differences["moisture"].append(
                _difference(
                    f"Water vapor at {level_label}",
                    before.qv_g_kg,
                    after.qv_g_kg,
                    "g/kg",
                    index,
                )
            )
        if not math.isclose(before.theta_k, after.theta_k):
            differences["stability/thermodynamics"].append(
                _difference(
                    f"Potential temperature at {level_label}",
                    before.theta_k,
                    after.theta_k,
                    "K",
                    index,
                )
            )
    if len(parent.sounding) != len(intended.sounding):
        differences["stability/thermodynamics"].append(
            _difference("Sounding level count", len(parent.sounding), len(intended.sounding), None)
        )
    if parent.duration_seconds != intended.duration_seconds:
        differences["numerics/time"].append(
            _difference(
                "Integration duration",
                parent.duration_seconds,
                intended.duration_seconds,
                "s",
            )
        )
    if parent.output_cadence_seconds != intended.output_cadence_seconds:
        differences["output"].append(
            _difference(
                "Saved-output cadence",
                parent.output_cadence_seconds,
                intended.output_cadence_seconds,
                "s",
            )
        )
    return differences


def configuration_warnings(
    configuration: MountainWavesConfiguration,
    differences: dict[str, list[dict[str, Any]]],
) -> list[str]:
    warnings: list[str] = []
    saturated = [
        level.height_m
        for level in configuration.sounding
        if _relative_humidity_percent(level) >= 100.0
    ]
    if saturated:
        warnings.append(
            "The initial sounding is saturated or supersaturated at "
            f"{len(saturated)} level(s); cloud may exist at model start."
        )
    unstable = [value for value in _stability_profile(configuration.sounding) if value < 0.0]
    if unstable:
        warnings.append(
            "The edited potential-temperature profile contains "
            f"{len(unstable)} statically unstable layer(s)."
        )
    wind = [level.u_m_s for level in configuration.sounding]
    if min(wind) < 0.0 < max(wind):
        warnings.append("The cross-ridge wind profile reverses direction with height.")
    if any(abs(right - left) >= 15.0 for left, right in zip(wind, wind[1:], strict=False)):
        warnings.append(
            "The edited wind profile contains a layer with at least 15 m/s shear "
            "between sounding levels."
        )
    max_slope = (
        9.0
        * configuration.terrain.height_m
        / (8.0 * math.sqrt(3.0) * configuration.terrain.half_width_m)
    )
    if max_slope >= 0.35:
        warnings.append(
            "The idealized ridge has a steep analytic maximum slope "
            f"({max_slope:.2f}); terrain-following grid compression may be strong."
        )
    if configuration.duration_seconds < 1_800:
        warnings.append(
            "The integration is short; a wave-cloud response may not have time to mature."
        )
    if configuration.output_cadence_seconds > 400:
        warnings.append(
            "The saved-output cadence is coarse and may hide rapid formation or "
            "evaporation changes."
        )
    changed_groups = sum(bool(values) for values in differences.values())
    if changed_groups > 1:
        warnings.append(
            "Multiple physical groups change together, so the result will not support "
            "a one-factor causal interpretation."
        )
    return warnings


def _configuration_from_parent(
    parent: MountainWavesSimulationRecord, manifest: RunManifest, manifest_path: Path
) -> MountainWavesConfiguration:
    retained = manifest.run_configuration.get("mountain_waves_configuration")
    if isinstance(retained, dict):
        return MountainWavesConfiguration.model_validate(retained)
    if parent.simulation_id != MOIST_SIMULATION_ID:
        return _dry_source_configuration(parent, manifest)
    run_dir = manifest_path.parent
    levels = _read_parent_sounding(run_dir / "input_sounding", run_dir / "case_manifest.json")
    return MountainWavesConfiguration(
        terrain=TerrainConfiguration(height_m=2_000.0, half_width_m=10_000.0, center_m=500.0),
        sounding=levels,
        duration_seconds=int(manifest.run_configuration.get("duration_seconds", 4_000)),
        output_cadence_seconds=int(manifest.run_configuration.get("output_cadence_seconds", 200)),
    )


def _fallback_configuration(
    parent: MountainWavesSimulationRecord, manifest: RunManifest
) -> MountainWavesConfiguration:
    domain = manifest.run_configuration.get("domain")
    active_top = 20_000.0
    if isinstance(domain, dict):
        configured_top = domain.get("active_top_m", domain.get("active_model_top_m"))
        if isinstance(configured_top, int | float):
            active_top = float(configured_top)
    return MountainWavesConfiguration(
        terrain=TerrainConfiguration(height_m=400.0, half_width_m=1_000.0, center_m=100.0),
        sounding=[
            SoundingLevel(
                height_m=0.0, pressure_pa=100_000.0, theta_k=288.0, qv_g_kg=0.0, u_m_s=10.0
            ),
            SoundingLevel(
                height_m=active_top / 2.0,
                pressure_pa=25_000.0,
                theta_k=320.0,
                qv_g_kg=0.0,
                u_m_s=10.0,
            ),
            SoundingLevel(
                height_m=active_top + 1_000.0,
                pressure_pa=5_000.0,
                theta_k=390.0,
                qv_g_kg=0.0,
                u_m_s=10.0,
            ),
        ],
        duration_seconds=int(manifest.run_configuration.get("duration_seconds", 2_160)),
        output_cadence_seconds=int(manifest.run_configuration.get("output_cadence_seconds", 216)),
    )


def _dry_source_configuration(
    parent: MountainWavesSimulationRecord, manifest: RunManifest
) -> MountainWavesConfiguration:
    """Sample the pinned CM1 isnd=9 source formula onto editable profile levels."""
    domain = manifest.run_configuration.get("domain")
    active_top_m = 20_000.0
    dz_m = 200.0
    if isinstance(domain, dict):
        configured_top = domain.get("active_model_top_m", domain.get("active_top_m"))
        configured_dz = domain.get("dz_m")
        if isinstance(configured_top, int | float):
            active_top_m = float(configured_top)
        if isinstance(configured_dz, int | float):
            dz_m = float(configured_dz)
    heights = np.arange(0.0, active_top_m + dz_m + 0.1, dz_m)
    ns_s2 = 0.0001
    gravity_m_s2 = 9.81
    cp_j_kg_k = 1004.0
    rd_j_kg_k = 287.04
    theta_surface_k = 288.0
    theta = theta_surface_k * np.exp(ns_s2 * heights / gravity_m_s2)
    exner = 1.0 + gravity_m_s2**2 / (cp_j_kg_k * ns_s2 * theta_surface_k) * (
        np.exp(-ns_s2 * heights / gravity_m_s2) - 1.0
    )
    pressure = 100_000.0 * np.power(exner, cp_j_kg_k / rd_j_kg_k)
    terrain = parent.configuration.get("terrain") if parent.configuration else None
    terrain_configuration = TerrainConfiguration(
        height_m=float(terrain.get("height_m", 400.0)) if isinstance(terrain, dict) else 400.0,
        half_width_m=(
            float(terrain.get("half_width_m", 1_000.0)) if isinstance(terrain, dict) else 1_000.0
        ),
        center_m=float(terrain.get("center_m", 100.0)) if isinstance(terrain, dict) else 100.0,
    )
    return MountainWavesConfiguration(
        terrain=terrain_configuration,
        sounding=[
            SoundingLevel(
                height_m=float(height),
                pressure_pa=float(level_pressure),
                theta_k=float(level_theta),
                qv_g_kg=0.0,
                u_m_s=10.0,
            )
            for height, level_pressure, level_theta in zip(heights, pressure, theta, strict=True)
        ],
        duration_seconds=int(manifest.run_configuration.get("duration_seconds", 2_160)),
        output_cadence_seconds=int(manifest.run_configuration.get("output_cadence_seconds", 216)),
    )


def _parent_configuration_source(parent: MountainWavesSimulationRecord) -> str:
    if parent.simulation_id == MOIST_SIMULATION_ID:
        return "retained source-backed external sounding and terrain"
    if parent.role == "variation":
        return "retained exact parent variation configuration"
    return "pinned CM1 isnd=9 source formula sampled at native vertical spacing"


def _read_parent_sounding(sounding_path: Path, case_manifest_path: Path) -> list[SoundingLevel]:
    lines = [line.split() for line in sounding_path.read_text().splitlines() if line.strip()]
    if len(lines) < 3 or len(lines[0]) != 3:
        raise MountainWavesVariationError(
            "Parent input_sounding does not match the CM1 external profile format."
        )
    pressure_by_height: dict[int, float] = {}
    try:
        case_manifest = json.loads(case_manifest_path.read_text())
        rows = case_manifest["sounding_audit"]["rows"]
        pressure_by_height = {
            int(round(float(row["model_height_m"]))): float(row["pressure_pa"]) for row in rows
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        pressure_by_height = {}
    surface_pressure_pa = float(lines[0][0]) * 100.0
    levels = [
        SoundingLevel(
            height_m=0.0,
            pressure_pa=surface_pressure_pa,
            theta_k=float(lines[0][1]),
            qv_g_kg=float(lines[0][2]),
            u_m_s=float(lines[1][3]),
        )
    ]
    for row in lines[1:]:
        if len(row) != 5:
            raise MountainWavesVariationError("Parent sounding profile row is malformed.")
        height = float(row[0])
        pressure = pressure_by_height.get(
            int(round(height)), surface_pressure_pa * math.exp(-height / 8_000.0)
        )
        levels.append(
            SoundingLevel(
                height_m=height,
                pressure_pa=pressure,
                theta_k=float(row[1]),
                qv_g_kg=float(row[2]),
                u_m_s=float(row[3]),
                v_m_s=0.0,
            )
        )
    return levels


def _configuration_errors(
    request: MountainWavesVariationRequest,
    *,
    parent: MountainWavesConfiguration,
    inherited_domain: object,
    required_top_m: float,
) -> list[str]:
    configuration = request.configuration
    errors: list[str] = []
    name = request.simulation_name.strip()
    if not name:
        errors.append("A Simulation name is required before packaging.")
    elif len(name) > 80:
        errors.append("Simulation names must be 80 characters or fewer.")
    terrain = configuration.terrain
    if not 1.0 <= terrain.height_m <= 6_000.0:
        errors.append("Ridge height must be between 1 and 6,000 m.")
    if not 500.0 <= terrain.half_width_m <= 50_000.0:
        errors.append("Ridge half-width must be between 500 and 50,000 m.")
    domain_bounds = _domain_x_bounds(inherited_domain)
    if domain_bounds is None:
        errors.append("The inherited parent domain is unavailable for ridge-center validation.")
    elif not domain_bounds[0] <= terrain.center_m <= domain_bounds[1]:
        errors.append(
            "Ridge center must remain inside the inherited parent domain "
            f"({domain_bounds[0]:g} to {domain_bounds[1]:g} m)."
        )
    if configuration.duration_seconds < 600 or configuration.duration_seconds > 14_400:
        errors.append("Integration duration must be between 600 and 14,400 s.")
    cadence = configuration.output_cadence_seconds
    if cadence < 25 or cadence > configuration.duration_seconds:
        errors.append("Saved-output cadence must be at least 25 s and no longer than the run.")
    elif configuration.duration_seconds % cadence:
        errors.append("Saved-output cadence must divide the integration duration exactly.")
    if configuration.sounding[-1].height_m < required_top_m:
        errors.append(
            "The final sounding level must reach the parent profile top "
            f"({required_top_m / 1_000.0:g} km)."
        )
    if len(configuration.sounding) != len(parent.sounding) or any(
        not math.isclose(level.height_m, parent_level.height_m)
        or not math.isclose(level.pressure_pa, parent_level.pressure_pa)
        for level, parent_level in zip(configuration.sounding, parent.sounding, strict=False)
    ):
        errors.append(
            "Sounding heights and pressures are inherited from the parent and cannot be changed."
        )
    for level in configuration.sounding:
        if not 150.0 <= level.theta_k <= 800.0:
            errors.append(f"Potential temperature at {level.height_m:g} m is outside 150-800 K.")
        if not 0.0 <= level.qv_g_kg <= 30.0:
            errors.append(f"Water vapor at {level.height_m:g} m is outside 0-30 g/kg.")
        if not -100.0 <= level.u_m_s <= 100.0:
            errors.append(f"Cross-ridge wind at {level.height_m:g} m is outside -100 to 100 m/s.")
    return errors


def _domain_x_bounds(domain: object) -> tuple[float, float] | None:
    if not isinstance(domain, dict):
        return None
    nx = domain.get("nx")
    dx_m = domain.get("dx_m")
    if not isinstance(nx, int | float) or not isinstance(dx_m, int | float):
        return None
    if int(nx) < 2 or float(dx_m) <= 0.0:
        return None
    half_span = (int(nx) - 1) * float(dx_m) / 2.0
    return -half_span, half_span


def _render_variation_namelist(parent_text: str, configuration: MountainWavesConfiguration) -> str:
    assignments = parse_namelist_assignments(parent_text)
    replacements = {
        "timax": f"{configuration.duration_seconds:.1f}",
        "tapfrq": f"{configuration.output_cadence_seconds:.1f}",
        "itern": "4",
        "isnd": "7",
        "iwnd": "0",
        "imoist": "1",
        "output_zs": "1",
        "output_zh": "1",
        "output_th": "1",
        "output_prs": "1",
        "output_qv": "1",
        "output_q": "1",
        "output_uinterp": "1",
        "output_vinterp": "1",
        "output_winterp": "1",
        "output_w": "1",
    }
    missing = sorted(set(replacements) - set(assignments))
    if missing:
        raise MountainWavesVariationError(f"Parent namelist lacks required assignments: {missing}")
    rendered = parent_text
    for name, value in replacements.items():
        if parse_namelist_assignments(rendered)[name] != value:
            rendered = replace_namelist_assignment(rendered, name, value)
    return rendered


def _render_input_sounding(levels: list[SoundingLevel]) -> str:
    surface = levels[0]
    lines = [f"{surface.pressure_pa / 100.0:.4f} {surface.theta_k:.6f} {surface.qv_g_kg:.9f}"]
    for level in levels[1:]:
        lines.append(
            f"{level.height_m:.1f} {level.theta_k:.6f} {level.qv_g_kg:.9f} "
            f"{level.u_m_s:.6f} 0.000000"
        )
    return "\n".join(lines) + "\n"


def _write_terrain_file(
    path: Path, namelist: str, configuration: MountainWavesConfiguration
) -> dict[str, Any]:
    assignments = parse_namelist_assignments(namelist)
    nx = int(float(assignments["nx"]))
    ny = int(float(assignments["ny"]))
    dx_m = float(assignments["dx"])
    if ny != 1:
        raise MountainWavesVariationError("Mountain Waves variations require native ny=1.")
    x = (np.arange(nx, dtype=np.float64) - (nx - 1) / 2.0) * dx_m
    terrain = configuration.terrain.height_m / (
        1.0 + ((x - configuration.terrain.center_m) / configuration.terrain.half_width_m) ** 2
    )
    encoded = np.asarray(terrain[None, :], dtype="<f4")
    path.write_bytes(encoded.tobytes(order="C"))
    decoded = np.fromfile(path, dtype="<f4").reshape((ny, nx))
    crest = int(np.argmax(decoded[0]))
    return {
        "formula": "height / (1 + ((x - center) / half_width)^2)",
        "shape": [ny, nx],
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "crest_x_m": float(x[crest]),
        "crest_height_m": float(decoded[0, crest]),
        "maximum_slope": 9.0
        * configuration.terrain.height_m
        / (8.0 * math.sqrt(3.0) * configuration.terrain.half_width_m),
        "all_values_finite": bool(np.isfinite(decoded).all()),
    }


def _domain_record(namelist: str) -> dict[str, Any]:
    assignments = parse_namelist_assignments(namelist)
    nz = int(float(assignments["nz"]))
    dz_m = float(assignments["dz"])
    return {
        "nx": int(float(assignments["nx"])),
        "ny": int(float(assignments["ny"])),
        "nz": nz,
        "dx_m": float(assignments["dx"]),
        "dy_m": float(assignments["dy"]),
        "dz_m": dz_m,
        "active_top_m": nz * dz_m,
    }


def _terrain_preview(
    configuration: MountainWavesConfiguration, *, points: int
) -> list[dict[str, float]]:
    extent = max(60_000.0, configuration.terrain.half_width_m * 6.0)
    x_values = np.linspace(-extent, extent, points)
    heights = configuration.terrain.height_m / (
        1.0
        + ((x_values - configuration.terrain.center_m) / configuration.terrain.half_width_m) ** 2
    )
    return [
        {"x_m": float(x_value), "height_m": float(height)}
        for x_value, height in zip(x_values, heights, strict=True)
    ]


def _relative_humidity_percent(level: SoundingLevel) -> float:
    pressure = level.pressure_pa
    temperature = level.theta_k * (pressure / 100_000.0) ** (287.05 / 1004.0)
    saturation_vapor_pressure = 611.2 * math.exp(
        17.67 * (temperature - 273.15) / (temperature - 29.65)
    )
    saturation_mixing_ratio = (
        0.622 * saturation_vapor_pressure / max(1.0, pressure - saturation_vapor_pressure)
    )
    return 100.0 * (level.qv_g_kg / 1_000.0) / max(1.0e-12, saturation_mixing_ratio)


def _stability_profile(levels: list[SoundingLevel]) -> list[float]:
    gravity = 9.80665
    values: list[float] = []
    for lower, upper in zip(levels, levels[1:], strict=False):
        dz = upper.height_m - lower.height_m
        mean_theta = 0.5 * (lower.theta_k + upper.theta_k)
        values.append(gravity / mean_theta * (upper.theta_k - lower.theta_k) / dz)
    return values


def _configuration_v_is_zero(run_configuration: dict[str, Any]) -> bool:
    configuration = run_configuration.get("mountain_waves_configuration")
    if not isinstance(configuration, dict):
        return False
    sounding = configuration.get("sounding")
    return isinstance(sounding, list) and all(
        isinstance(level, dict) and float(level.get("v_m_s", math.nan)) == 0.0 for level in sounding
    )


def _empty_differences() -> dict[str, list[dict[str, Any]]]:
    return {group: [] for group in DIFFERENCE_GROUPS}


def _difference(
    label: str, before: object, after: object, units: str | None, level_index: int | None = None
) -> dict[str, Any]:
    return {
        "label": label,
        "before": before,
        "after": after,
        "units": units,
        "level_index": level_index,
    }


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "variation")[:40]


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
