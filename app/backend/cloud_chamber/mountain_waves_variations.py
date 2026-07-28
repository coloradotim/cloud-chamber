"""Durable Mountain Waves variation envelopes and deterministic packaging."""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
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
from cloud_chamber.mountain_waves_recipes import (
    BOULDER_RECIPE_ID,
    DRY_RECIPE_ID,
    RECIPE_CONTRACT_VERSION,
    RUN_COST_RECIPE_VERSION,
    MountainWavesRecipeControls,
    RecipeId,
    RecipeSoundingLevel,
    ResolvedMountainWavesRecipe,
    default_controls,
    recipe_name,
    resolve_mountain_waves_recipe,
)
from cloud_chamber.mountain_waves_world import (
    DRY_SIMULATION_ID,
    MOIST_SIMULATION_ID,
    WORLD_ID,
    MountainWavesSimulationRecord,
    mountain_waves_run_manifest,
)
from cloud_chamber.run_cost import (
    RunCostEstimate,
    create_launch_review_snapshot,
    estimate_profile,
    profile_by_id,
    profiles,
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
from cloud_chamber.storage_policy import DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES
from cloud_chamber.variation_envelope import (
    VariationDifference,
    VariationEnvelope,
    VariationValidationDecision,
    canonical_payload_sha256,
    classify_relationship,
    grouped_differences,
    immutable_layer,
)

VARIATION_CASE_ID = "mountain_waves_recipe_variation_v1"
LEGACY_VARIATION_CASE_ID = "mountain_waves_exploratory_variation_v1"
VARIATION_SCHEMA_VERSION = "mountain_waves_variation_v2"
DIFFERENCE_GROUPS = (
    "terrain",
    "wind",
    "moisture",
    "stability/thermodynamics",
    "forcing/initiation",
    "numerical realization",
    "observation plan",
)


class MountainWavesVariationError(RuntimeError):
    """Raised when an approved Mountain Waves variation cannot be represented honestly."""


class MountainWavesVariationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str = MOIST_SIMULATION_ID
    simulation_name: str
    user_question: str | None = None
    recipe_id: RecipeId
    run_profile_id: str
    controls: MountainWavesRecipeControls

    @model_validator(mode="after")
    def validate_recipe_identity(self) -> MountainWavesVariationRequest:
        if self.controls.recipe_id != self.recipe_id:
            raise ValueError("Request Recipe and control payload Recipe must match.")
        return self


class MountainWavesVariationTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str
    parent_run_id: str
    parent_display_name: str
    parent_configuration_source: str
    reference_simulation_id: str
    recipe_id: RecipeId
    recipe_name: str
    recipe_contract_version: str = RECIPE_CONTRACT_VERSION
    controls: MountainWavesRecipeControls
    run_profiles: list[RunCostEstimate]
    default_run_profile_id: str
    can_create_variation: bool
    unavailable_reason: str | None = None


class MountainWavesVariationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: RecipeId
    recipe_name: str
    differences: dict[str, list[dict[str, Any]]]
    relationship_classification: str | None
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: dict[str, Any]
    terrain_profile: list[dict[str, float]]
    wind_profile: list[dict[str, float]]
    moisture_profile: list[dict[str, float]]
    relative_humidity_profile: list[dict[str, float]]
    theta_profile: list[dict[str, float]]
    stability_profile: list[dict[str, float]]
    numerical_realization: dict[str, Any]
    observation_plan: dict[str, Any]
    cost_estimate: RunCostEstimate


class MountainWavesVariationPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    run_id: str
    manifest_path: str
    package_dir: str
    envelope: VariationEnvelope
    differences: dict[str, list[dict[str, Any]]]
    warnings: list[str]
    preflight: dict[str, Any]
    launch_review_snapshot_id: str


class _VariationContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    template: MountainWavesVariationTemplate
    parent: MountainWavesSimulationRecord
    parent_manifest: RunManifest
    parent_manifest_path: Path
    reference_controls: MountainWavesRecipeControls
    reference_sounding: list[RecipeSoundingLevel]
    parent_profile_id: str


def mountain_waves_variation_template(
    settings: CloudChamberSettings, parent_simulation_id: str
) -> MountainWavesVariationTemplate:
    return _variation_context(settings, parent_simulation_id).template


def preview_mountain_waves_variation(
    settings: CloudChamberSettings, request: MountainWavesVariationRequest
) -> MountainWavesVariationPreview:
    context = _variation_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(settings, request, context)
    errors = _request_errors(request, context, resolved, differences)
    relationship = _relationship(differences)
    return MountainWavesVariationPreview(
        recipe_id=request.recipe_id,
        recipe_name=resolved.recipe_name,
        differences=grouped_differences(differences),
        relationship_classification=relationship,
        warnings=_dedupe(resolved.warnings),
        blocking_errors=_dedupe(errors),
        diagnostics=resolved.diagnostics.model_dump(mode="json"),
        terrain_profile=resolved.terrain_profile,
        wind_profile=resolved.wind_profile,
        moisture_profile=resolved.moisture_profile,
        relative_humidity_profile=resolved.relative_humidity_profile,
        theta_profile=resolved.theta_profile,
        stability_profile=resolved.stability_profile,
        numerical_realization=resolved.numerical_realization.model_dump(mode="json"),
        observation_plan=resolved.observation_plan.model_dump(mode="json"),
        cost_estimate=estimate_profile(settings, resolved.resolved_cost_profile),
    )


def create_mountain_waves_variation(
    settings: CloudChamberSettings, request: MountainWavesVariationRequest
) -> MountainWavesVariationPackage:
    context = _variation_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(settings, request, context)
    errors = _request_errors(request, context, resolved, differences)
    if errors:
        raise MountainWavesVariationError(" ".join(_dedupe(errors)))
    implementation_commit = verified_clean_git_commit()
    provenance = collect_cm1_provenance(settings)

    scientific_design: dict[str, Any] = {
        "world_id": WORLD_ID,
        "recipe_id": request.recipe_id,
        "recipe_contract_version": RECIPE_CONTRACT_VERSION,
        "reference_simulation_id": context.template.reference_simulation_id,
        "controls": request.controls.payload(),
        "fixed_assumptions": {
            "native_geometry": "two-dimensional x-z with singleton y",
            "terrain_shape": "authored bell ridge",
            "v_wind_m_s": 0.0,
            "recipe_reference_transform": True,
        },
    }
    numerical_payload = resolved.numerical_realization.model_dump(mode="json")
    observation_payload = resolved.observation_plan.model_dump(mode="json")
    identity_payload = {
        "parent_simulation_id": context.parent.simulation_id,
        "scientific_design": scientific_design,
        "numerical_realization": numerical_payload,
        "observation_plan": observation_payload,
    }
    identity = canonical_payload_sha256(identity_payload)
    slug = _slug(request.simulation_name)
    simulation_id = f"mountain_waves_{slug}_{identity[:8]}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt_suffix = uuid4().hex[:4]
    run_id = f"mw-{slug}-{timestamp}-{attempt_suffix}"
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
        parent_run_dir = Path(context.parent_manifest.generated_inputs.run_directory).expanduser()
        parent_namelist = parent_run_dir / "namelist.input"
        if not parent_namelist.is_file():
            raise MountainWavesVariationError("The parent namelist is unavailable.")
        namelist = _render_variation_namelist(parent_namelist.read_text(), resolved)
        paths["namelist"].write_text(namelist)
        paths["sounding"].write_text(_render_input_sounding(resolved.sounding))
        terrain_audit = _write_terrain_file(paths["terrain"], namelist, resolved.terrain)
        _write_json(
            paths["runtime_checklist"],
            {
                "status": "exact_recipe_inputs_present",
                "consumed_files": ["input_sounding", "perts.dat"],
                "required_files": [],
                "source_candidates": {},
            },
        )
        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key in {"namelist", "sounding", "terrain", "runtime_checklist"}
        }
        now = datetime.now(UTC)
        relationship = classify_relationship(differences)
        cost_estimate = estimate_profile(settings, resolved.resolved_cost_profile)
        reference_simulation_id = context.template.reference_simulation_id
        envelope = VariationEnvelope(
            world_id=WORLD_ID,
            recipe_id=request.recipe_id,
            recipe_contract_version=RECIPE_CONTRACT_VERSION,
            simulation_id=simulation_id,
            parent_simulation_id=context.parent.simulation_id,
            reference_simulation_id=reference_simulation_id,
            display_name=request.simulation_name.strip(),
            question=_optional_text(request.user_question),
            scientific_design=immutable_layer(scientific_design),
            numerical_realization=immutable_layer(numerical_payload),
            observation_plan=immutable_layer(observation_payload),
            world_payload={
                "controls": request.controls.model_dump(mode="json"),
                "terrain": resolved.terrain,
                "sounding_generator": (
                    "dry_ridge_analytic_v1"
                    if request.recipe_id == DRY_RECIPE_ID
                    else "boulder_source_backed_transform_v1"
                ),
                "diagnostics": resolved.diagnostics.model_dump(mode="json"),
            },
            differences=differences,
            relationship_classification=relationship,
            run_profile_id=request.run_profile_id,
            run_profile_contract=resolved.resolved_cost_profile.model_dump(mode="json"),
            cost_estimate=cost_estimate.model_dump(mode="json"),
            package_identity_sha256=identity,
            validation_decisions=[
                VariationValidationDecision(
                    stage="specification",
                    disposition="passed",
                    reason="Controls and generated design are inside Recipe contract version 1.",
                ),
                VariationValidationDecision(
                    stage="package",
                    disposition="pending",
                    reason="Exact generated-input hashes are verified after package write.",
                ),
                VariationValidationDecision(
                    stage="availability",
                    disposition="pending",
                    reason="Availability requires complete inspectable native output.",
                ),
                VariationValidationDecision(
                    stage="parent_eligibility",
                    disposition="pending",
                    reason="Parent eligibility is distinct from availability.",
                ),
            ],
            availability_state="packaged",
        )
        launch_specification = {
            "world_id": WORLD_ID,
            "recipe_id": request.recipe_id,
            "recipe_version": RUN_COST_RECIPE_VERSION,
            "profile_id": request.run_profile_id,
            "numerical_realization": numerical_payload,
            "observation_plan": observation_payload,
        }
        run_configuration: dict[str, Any] = {
            "cloud_world_id": WORLD_ID,
            "simulation_id": simulation_id,
            "simulation_display_name": request.simulation_name.strip(),
            "parent_simulation_id": context.parent.simulation_id,
            "parent_run_id": context.parent.run_id,
            "reference_simulation_id": reference_simulation_id,
            "user_question": _optional_text(request.user_question),
            "variation_envelope": envelope.model_dump(mode="json"),
            "mountain_waves_configuration": {
                "terrain": resolved.terrain,
                "sounding": [level.model_dump(mode="json") for level in resolved.sounding],
                "duration_seconds": resolved.observation_plan.duration_seconds,
                "output_cadence_seconds": resolved.observation_plan.output_cadence_seconds,
            },
            "configuration_difference": grouped_differences(differences),
            "warnings": resolved.warnings,
            "duration_seconds": resolved.observation_plan.duration_seconds,
            "output_cadence_seconds": resolved.observation_plan.output_cadence_seconds,
            "expected_model_output_count": resolved.observation_plan.expected_history_count,
            "domain": _domain_record(namelist),
            "terrain": resolved.terrain,
            "terrain_audit": terrain_audit,
            "generated_input_sha256": generated_hashes,
            "parent_manifest_path": str(context.parent_manifest_path),
            "cm1_provenance": provenance.report_record(),
            "launch_specification": launch_specification,
        }
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(
                id=VARIATION_CASE_ID, schema_version=VARIATION_SCHEMA_VERSION
            ),
            controls=_manifest_controls(request.controls.payload()),
            run_configuration=run_configuration,
            physical_question=(
                _optional_text(request.user_question)
                or f"How does {request.simulation_name.strip()} differ from its parent?"
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
                "status": "passed",
                "blocking_errors": [],
                "caveats": resolved.warnings,
                "relationship_classification": relationship,
                "configuration_difference": grouped_differences(differences),
                "package_path": "shared_variation_envelope_v1",
            },
            run_recipe=request.recipe_id,
            run_recipe_display_name=resolved.recipe_name,
            recipe_id=request.recipe_id,
            recipe_display_name=resolved.recipe_name,
            assumption_set_id=f"{request.recipe_id}_contract_v1",
            assumption_mode="approved_recipe_contract",
            recipe_assumptions=scientific_design["fixed_assumptions"],
            required_output_fields=list(resolved.observation_plan.retained_field_inventory),
            input_source=(
                "exact_dry_ridge_analytic_generator_v1"
                if request.recipe_id == DRY_RECIPE_ID
                else "boulder_reference_source_backed_transform_v1"
            ),
            expected_outputs=["native_numbered_cm1_model_netcdf", "cm1_stats_and_logs"],
            run_caveats=resolved.warnings,
            manual_validation_status="approved_recipe_variation_packaged",
        )
        write_run_manifest(paths["manifest"], manifest)
        case_manifest = {
            "schema_version": VARIATION_SCHEMA_VERSION,
            "variation_envelope": envelope.model_dump(mode="json"),
            "implementation_commit": implementation_commit,
            "run_id": run_id,
            "generated_input_sha256": generated_hashes,
            "terrain_audit": terrain_audit,
            "cm1_provenance": provenance.report_record(),
        }
        _write_json(paths["case_manifest"], case_manifest)
        _write_json(
            paths["package_report"],
            {
                "status": "packaged_not_queued",
                **case_manifest,
            },
        )
        preflight = preflight_mountain_waves_variation(paths["manifest"])
        manifest = load_run_manifest(paths["manifest"])
        snapshot = create_launch_review_snapshot(
            settings,
            profile_id=request.run_profile_id,
            warning_threshold_bytes=DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
            manifest=manifest,
            resolved_profile=resolved.resolved_cost_profile,
        )
        snapshot_id = snapshot.snapshot.snapshot_id
        envelope.launch_review_snapshot_id = snapshot_id
        envelope.validation_decisions[1] = VariationValidationDecision(
            stage="package",
            disposition="passed",
            reason="Exact generated-input hashes and package preflight passed.",
        )
        run_configuration["launch_review_snapshot_id"] = snapshot_id
        run_configuration["variation_envelope"] = envelope.model_dump(mode="json")
        manifest.run_configuration = run_configuration
        manifest.updated_at = datetime.now(UTC)
        write_run_manifest(paths["manifest"], manifest)
        return MountainWavesVariationPackage(
            simulation_id=simulation_id,
            run_id=run_id,
            manifest_path=str(paths["manifest"]),
            package_dir=str(package_dir),
            envelope=envelope,
            differences=grouped_differences(differences),
            warnings=resolved.warnings,
            preflight=preflight,
            launch_review_snapshot_id=snapshot_id,
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
    envelope = _manifest_envelope(manifest)
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
        "shared_envelope": envelope.schema_version == "cloud_world_variation_v1",
        "required_inputs_present": not missing,
        "generated_hashes_match": bool(hash_checks) and all(hash_checks.values()),
        "no_existing_cm1_output": not outputs,
        "two_dimensional_v_zero": _configuration_v_is_zero(manifest.run_configuration),
        "launch_specification_bound": isinstance(
            manifest.run_configuration.get("launch_specification"), dict
        ),
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


def _variation_context(
    settings: CloudChamberSettings, parent_simulation_id: str
) -> _VariationContext:
    parent, manifest, manifest_path = mountain_waves_run_manifest(settings, parent_simulation_id)
    recipe_id = _parent_recipe_id(parent, manifest)
    reference_simulation_id = (
        DRY_SIMULATION_ID if recipe_id == DRY_RECIPE_ID else MOIST_SIMULATION_ID
    )
    reference_controls = default_controls(recipe_id)
    parent_controls = _parent_controls(manifest, recipe_id)
    reference_sounding = _reference_sounding(settings, recipe_id)
    parent_profile_id = _parent_profile_id(manifest, recipe_id)
    recipe_profiles = [
        profile
        for profile in profiles()
        if profile.world_id == WORLD_ID and profile.recipe_id == recipe_id
    ]
    estimates = [estimate_profile(settings, profile) for profile in recipe_profiles]
    can_create, reason = _parent_eligibility(parent, manifest, recipe_id)
    available_profile_ids = {profile.profile_id for profile in recipe_profiles}
    default_profile = (
        parent_profile_id
        if parent_profile_id in available_profile_ids
        else next(
            (profile.profile_id for profile in recipe_profiles if profile.role == "Standard"),
            recipe_profiles[0].profile_id if recipe_profiles else "",
        )
    )
    template = MountainWavesVariationTemplate(
        parent_simulation_id=parent.simulation_id,
        parent_run_id=parent.run_id,
        parent_display_name=parent.display_name,
        parent_configuration_source=_parent_configuration_source(parent, recipe_id),
        reference_simulation_id=reference_simulation_id,
        recipe_id=recipe_id,
        recipe_name=recipe_name(recipe_id),
        controls=parent_controls,
        run_profiles=estimates,
        default_run_profile_id=default_profile,
        can_create_variation=can_create,
        unavailable_reason=reason,
    )
    return _VariationContext(
        template=template,
        parent=parent,
        parent_manifest=manifest,
        parent_manifest_path=manifest_path,
        reference_controls=reference_controls,
        reference_sounding=reference_sounding,
        parent_profile_id=parent_profile_id,
    )


def _resolve_request(
    settings: CloudChamberSettings,
    request: MountainWavesVariationRequest,
    context: _VariationContext,
) -> tuple[ResolvedMountainWavesRecipe, list[VariationDifference]]:
    if request.recipe_id != context.template.recipe_id:
        raise MountainWavesVariationError("The selected parent and requested Recipe do not match.")
    try:
        catalog_profile = profile_by_id(request.run_profile_id)
    except ValueError as exc:
        raise MountainWavesVariationError(str(exc)) from exc
    resolved = resolve_mountain_waves_recipe(
        controls=request.controls,
        reference_controls=context.reference_controls,
        reference_sounding=context.reference_sounding,
        catalog_profile=catalog_profile,
    )
    differences = list(resolved.differences)
    if request.run_profile_id != context.parent_profile_id:
        differences.extend(
            [
                VariationDifference(
                    category="numerical_realization",
                    path="run_profile_id",
                    label="Run profile",
                    before=context.parent_profile_id,
                    after=request.run_profile_id,
                ),
                VariationDifference(
                    category="observation_plan",
                    path="observation_plan",
                    label="Observation plan",
                    before=context.parent_profile_id,
                    after=request.run_profile_id,
                ),
            ]
        )
    return resolved, differences


def _request_errors(
    request: MountainWavesVariationRequest,
    context: _VariationContext,
    resolved: ResolvedMountainWavesRecipe,
    differences: list[VariationDifference],
) -> list[str]:
    errors = list(resolved.blocking_errors)
    if not context.template.can_create_variation:
        errors.append(context.template.unavailable_reason or "The selected parent is not eligible.")
    name = request.simulation_name.strip()
    if not name:
        errors.append("A Simulation name is required before packaging.")
    elif len(name) > 80:
        errors.append("Simulation names must be 80 characters or fewer.")
    if not differences:
        errors.append(
            "Change at least one Recipe control or explicitly select a different run profile."
        )
    return errors


def _parent_recipe_id(parent: MountainWavesSimulationRecord, manifest: RunManifest) -> RecipeId:
    envelope_payload = manifest.run_configuration.get("variation_envelope")
    if isinstance(envelope_payload, dict):
        recipe_id = envelope_payload.get("recipe_id")
        if recipe_id in {DRY_RECIPE_ID, BOULDER_RECIPE_ID}:
            return cast(RecipeId, recipe_id)
    if parent.simulation_id == DRY_SIMULATION_ID:
        return DRY_RECIPE_ID
    return BOULDER_RECIPE_ID


def _parent_controls(manifest: RunManifest, recipe_id: RecipeId) -> MountainWavesRecipeControls:
    envelope_payload = manifest.run_configuration.get("variation_envelope")
    if isinstance(envelope_payload, dict):
        world_payload = envelope_payload.get("world_payload")
        if isinstance(world_payload, dict) and isinstance(world_payload.get("controls"), dict):
            try:
                controls = MountainWavesRecipeControls.model_validate(world_payload["controls"])
            except ValueError:
                controls = None
            if controls is not None and controls.recipe_id == recipe_id:
                return controls
    return default_controls(recipe_id)


def _reference_sounding(
    settings: CloudChamberSettings, recipe_id: RecipeId
) -> list[RecipeSoundingLevel]:
    if recipe_id == DRY_RECIPE_ID:
        return []
    _record, manifest, manifest_path = mountain_waves_run_manifest(settings, MOIST_SIMULATION_ID)
    return _read_parent_sounding(
        manifest_path.parent / "input_sounding",
        manifest_path.parent / "case_manifest.json",
    )


def _parent_profile_id(manifest: RunManifest, recipe_id: RecipeId) -> str:
    envelope_payload = manifest.run_configuration.get("variation_envelope")
    if isinstance(envelope_payload, dict):
        profile_id = envelope_payload.get("run_profile_id")
        if isinstance(profile_id, str):
            return profile_id
    return (
        "mountain_waves_dry_presentation_v1"
        if recipe_id == DRY_RECIPE_ID
        else "mountain_waves_boulder_presentation_v1"
    )


def _parent_eligibility(
    parent: MountainWavesSimulationRecord, manifest: RunManifest, recipe_id: RecipeId
) -> tuple[bool, str | None]:
    if not parent.inspectable:
        return False, "Only an available, inspectable Simulation can be a variation parent."
    if parent.role == "built_in":
        return True, None
    try:
        envelope = _manifest_envelope(manifest)
    except MountainWavesVariationError:
        return (
            False,
            "This remains an inspectable Legacy-contract Simulation, but it is not "
            "eligible to parent a new Recipe variation.",
        )
    if envelope.recipe_id != recipe_id or not envelope.parent_eligible:
        return (
            False,
            envelope.parent_eligibility_reason
            or "This Simulation is available but not parent-eligible.",
        )
    return True, None


def _manifest_envelope(manifest: RunManifest) -> VariationEnvelope:
    payload = manifest.run_configuration.get("variation_envelope")
    if not isinstance(payload, dict):
        raise MountainWavesVariationError("This variation predates the shared Recipe envelope.")
    try:
        return VariationEnvelope.model_validate(payload)
    except ValueError as exc:
        raise MountainWavesVariationError("Variation envelope is invalid.") from exc


def _parent_configuration_source(parent: MountainWavesSimulationRecord, recipe_id: RecipeId) -> str:
    if recipe_id == DRY_RECIPE_ID:
        return "hash-locked Dry Ridge analytic Recipe generator"
    if parent.role == "built_in":
        return "retained Boulder source-backed atmosphere and terrain"
    return "retained Recipe controls resolved against the Boulder reference"


def _read_parent_sounding(
    sounding_path: Path, case_manifest_path: Path
) -> list[RecipeSoundingLevel]:
    lines = [line.split() for line in sounding_path.read_text().splitlines() if line.strip()]
    if len(lines) < 3 or len(lines[0]) != 3:
        raise MountainWavesVariationError(
            "Reference input_sounding does not match the CM1 external profile format."
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
        RecipeSoundingLevel(
            height_m=0.0,
            pressure_pa=surface_pressure_pa,
            theta_k=float(lines[0][1]),
            qv_g_kg=float(lines[0][2]),
            u_m_s=float(lines[1][3]),
        )
    ]
    for row in lines[1:]:
        if len(row) != 5:
            raise MountainWavesVariationError("Reference sounding profile row is malformed.")
        height = float(row[0])
        if height <= levels[-1].height_m:
            continue
        pressure = pressure_by_height.get(
            int(round(height)), surface_pressure_pa * math.exp(-height / 8_000.0)
        )
        levels.append(
            RecipeSoundingLevel(
                height_m=height,
                pressure_pa=pressure,
                theta_k=float(row[1]),
                qv_g_kg=float(row[2]),
                u_m_s=float(row[3]),
                v_m_s=0.0,
            )
        )
    return levels


def _render_variation_namelist(parent_text: str, resolved: ResolvedMountainWavesRecipe) -> str:
    numerical = resolved.numerical_realization
    grid_match = re.fullmatch(r"(\d+) × 1 × (\d+)", numerical.grid)
    spacing_match = re.fullmatch(r"([0-9.]+) × ([0-9.]+) m", numerical.spacing)
    timestep_match = re.search(r"([0-9.]+)", numerical.timestep_strategy)
    if not grid_match or not spacing_match or not timestep_match:
        raise MountainWavesVariationError("Resolved numerical realization is malformed.")
    nx, nz = (int(value) for value in grid_match.groups())
    dx_m, dz_m = (float(value) for value in spacing_match.groups())
    duration = resolved.observation_plan.duration_seconds
    cadence = resolved.observation_plan.output_cadence_seconds
    if duration is None or cadence is None:
        raise MountainWavesVariationError("Resolved observation plan is incomplete.")
    replacements = {
        "nx": str(nx),
        "ny": "1",
        "nz": str(nz),
        "dx": f"{dx_m:g}",
        "dy": f"{dx_m:g}",
        "dz": f"{dz_m:g}",
        "dtl": timestep_match.group(1),
        "timax": f"{duration:g}",
        "tapfrq": f"{cadence:g}",
        "itern": "4",
        "isnd": "7",
        "iwnd": "0",
        "imoist": "0" if resolved.recipe_id == DRY_RECIPE_ID else "1",
        "zd": f"{resolved.diagnostics.damping_base_m:g}",
        "ztop": f"{resolved.diagnostics.model_top_m:g}",
        "stretch_z": "0",
        "output_zs": "1",
        "output_zh": "1",
        "output_th": "1",
        "output_prs": "1",
        "output_uinterp": "1",
        "output_vinterp": "1",
        "output_winterp": "1",
        "output_w": "1",
    }
    if resolved.recipe_id == BOULDER_RECIPE_ID:
        replacements.update({"output_qv": "1", "output_q": "1"})
    assignments = parse_namelist_assignments(parent_text)
    missing = sorted(set(replacements) - set(assignments))
    if missing:
        raise MountainWavesVariationError(f"Parent namelist lacks required assignments: {missing}")
    rendered = parent_text
    for name, value in replacements.items():
        if parse_namelist_assignments(rendered)[name] != value:
            rendered = replace_namelist_assignment(rendered, name, value)
    return rendered


def _render_input_sounding(levels: list[RecipeSoundingLevel]) -> str:
    surface = levels[0]
    lines = [f"{surface.pressure_pa / 100.0:.4f} {surface.theta_k:.6f} {surface.qv_g_kg:.9f}"]
    for level in levels[1:]:
        lines.append(
            f"{level.height_m:.1f} {level.theta_k:.6f} {level.qv_g_kg:.9f} "
            f"{level.u_m_s:.6f} 0.000000"
        )
    return "\n".join(lines) + "\n"


def _write_terrain_file(
    path: Path, namelist: str, terrain_configuration: dict[str, float]
) -> dict[str, Any]:
    assignments = parse_namelist_assignments(namelist)
    nx = int(float(assignments["nx"]))
    ny = int(float(assignments["ny"]))
    dx_m = float(assignments["dx"])
    if ny != 1:
        raise MountainWavesVariationError("Mountain Waves variations require native ny=1.")
    x = (np.arange(nx, dtype=np.float64) - (nx - 1) / 2.0) * dx_m
    height_m = terrain_configuration["height_m"]
    half_width_m = terrain_configuration["half_width_m"]
    center_m = terrain_configuration["center_m"]
    terrain = height_m / (1.0 + ((x - center_m) / half_width_m) ** 2)
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
        "maximum_slope": 9.0 * height_m / (8.0 * math.sqrt(3.0) * half_width_m),
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


def _configuration_v_is_zero(run_configuration: dict[str, Any]) -> bool:
    configuration = run_configuration.get("mountain_waves_configuration")
    if not isinstance(configuration, dict):
        return False
    sounding = configuration.get("sounding")
    return isinstance(sounding, list) and all(
        isinstance(level, dict) and float(level.get("v_m_s", math.nan)) == 0.0 for level in sounding
    )


def _relationship(differences: list[VariationDifference]) -> str | None:
    try:
        return classify_relationship(differences)
    except ValueError:
        return None


def _manifest_controls(controls: dict[str, Any]) -> dict[str, str | float | bool]:
    return {
        key: value for key, value in controls.items() if isinstance(value, str | float | int | bool)
    }


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:48] or "variation"


def _optional_text(value: str | None) -> str | None:
    stripped = value.strip() if value else ""
    return stripped or None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
