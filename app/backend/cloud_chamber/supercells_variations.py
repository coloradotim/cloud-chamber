"""Durable Supercells variation envelopes and deterministic packaging."""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    RunManifestError,
    RuntimePaths,
    ScenarioReference,
    UserMetadata,
    ValidationStatus,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storage_policy import DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES
from cloud_chamber.storm_examination import (
    PRESENTATION_CASE_ID,
    PRESENTATION_RUN_ID,
    QUARTER_CIRCLE_SIMULATION_ID,
    STRAIGHT_LINE_PRESENTATION_CASE_ID,
    STRAIGHT_LINE_PRESENTATION_RUN_ID,
    STRAIGHT_LINE_SIMULATION_ID,
)
from cloud_chamber.supercells_recipes import (
    RECIPE_CONTRACT_VERSION,
    RECIPE_ID,
    RECIPE_NAME,
    RUN_COST_RECIPE_VERSION,
    ResolvedSupercellsRecipe,
    SupercellsControls,
    SupercellsProfileLevel,
    default_controls,
    normalize_controls,
    resolve_supercells_recipe,
)
from cloud_chamber.supercells_source_customization import (
    SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME,
    SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
    load_supercells_source_customization,
    supercells_source_customization_artifact,
)
from cloud_chamber.variation_envelope import (
    AttemptRelationship,
    VariationAttempt,
    VariationDifference,
    VariationEnvelope,
    VariationValidationDecision,
    canonical_payload_sha256,
    classify_relationship,
    grouped_differences,
    immutable_layer,
)

WORLD_ID = "supercells"
REFERENCE_SIMULATION_ID = QUARTER_CIRCLE_SIMULATION_ID
VARIATION_CASE_ID = "supercells_recipe_variation_v1"
VARIATION_SCHEMA_VERSION = "supercells_variation_v1"


class SupercellsVariationError(RuntimeError):
    """Raised when a Supercells variation cannot satisfy the approved contract."""


class SupercellsVariationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str = REFERENCE_SIMULATION_ID
    simulation_name: str = Field(min_length=1, max_length=120)
    user_question: str | None = Field(default=None, max_length=500)
    recipe_id: str = RECIPE_ID
    run_profile_id: str
    controls: SupercellsControls

    @model_validator(mode="after")
    def validate_identity(self) -> SupercellsVariationRequest:
        if self.recipe_id != RECIPE_ID:
            raise ValueError("Supercells variations require the approved Recipe contract.")
        if not self.simulation_name.strip():
            raise ValueError("Variation name is required.")
        return self


class SupercellsVariationTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str
    parent_run_id: str
    parent_display_name: str
    parent_configuration_source: str
    reference_simulation_id: str = REFERENCE_SIMULATION_ID
    recipe_id: str = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    recipe_contract_version: str = RECIPE_CONTRACT_VERSION
    controls: SupercellsControls
    reference_controls: SupercellsControls
    run_profiles: list[RunCostEstimate]
    default_run_profile_id: str
    can_create_variation: bool
    unavailable_reason: str | None = None


class SupercellsVariationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    reference_controls: dict[str, Any]
    parent_controls: dict[str, Any]
    requested_controls: dict[str, Any]
    achieved_controls: dict[str, Any]
    differences: dict[str, list[dict[str, Any]]]
    relationship_classification: str | None
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: dict[str, Any]
    sounding: list[dict[str, Any]]
    hodograph: list[dict[str, float]]
    initiation: dict[str, float]
    numerical_realization: dict[str, Any]
    observation_plan: dict[str, Any]
    useful_window_end_seconds: int
    cost_estimate: RunCostEstimate


class SupercellsVariationPackage(BaseModel):
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


class _ParentContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    template: SupercellsVariationTemplate
    parent_manifest: RunManifest
    parent_manifest_path: Path
    parent_controls: SupercellsControls
    parent_numerical_realization: dict[str, Any]
    parent_observation_plan: dict[str, Any]


def supercells_variation_template(
    settings: CloudChamberSettings,
    parent_simulation_id: str,
) -> SupercellsVariationTemplate:
    return _parent_context(settings, parent_simulation_id).template


def preview_supercells_variation(
    settings: CloudChamberSettings,
    request: SupercellsVariationRequest,
) -> SupercellsVariationPreview:
    context = _parent_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(request, context)
    errors = _request_errors(settings, request, context, resolved, differences)
    return SupercellsVariationPreview(
        reference_controls=default_controls().model_dump(mode="json"),
        parent_controls=context.parent_controls.model_dump(mode="json"),
        requested_controls=request.controls.model_dump(mode="json"),
        achieved_controls=resolved.achieved_controls,
        differences=grouped_differences(differences),
        relationship_classification=_relationship(differences),
        warnings=_dedupe(resolved.warnings),
        blocking_errors=_dedupe(errors),
        diagnostics=resolved.diagnostics.model_dump(mode="json"),
        sounding=[level.model_dump(mode="json") for level in resolved.sounding],
        hodograph=[level.model_dump(mode="json") for level in resolved.hodograph],
        initiation=resolved.initiation,
        numerical_realization=resolved.resolved_cost_profile.numerical_realization.model_dump(
            mode="json"
        ),
        observation_plan=resolved.observation_plan.model_dump(mode="json"),
        useful_window_end_seconds=_useful_window_end_seconds(
            request.run_profile_id,
            int(resolved.observation_plan.duration_seconds or 0),
        ),
        cost_estimate=estimate_profile(settings, resolved.resolved_cost_profile),
    )


def create_supercells_variation(
    settings: CloudChamberSettings,
    request: SupercellsVariationRequest,
) -> SupercellsVariationPackage:
    context = _parent_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(request, context)
    errors = _request_errors(settings, request, context, resolved, differences)
    if errors:
        raise SupercellsVariationError(" ".join(_dedupe(errors)))
    implementation_commit = verified_clean_git_commit()
    provenance = collect_cm1_provenance(settings)
    numerical_payload = resolved.resolved_cost_profile.numerical_realization.model_dump(mode="json")
    observation_payload = resolved.observation_plan.model_dump(mode="json")
    useful_window_end_seconds = _useful_window_end_seconds(
        request.run_profile_id,
        int(resolved.observation_plan.duration_seconds or 0),
    )
    fixed_assumptions: dict[str, Any] = {
        "horizontally_homogeneous_environment": True,
        "microphysics": "Morrison double-moment",
        "terrain": "flat",
        "surface_heat_moisture_forcing": False,
        "single_deterministic_thermal": True,
        "storm_object_lineage": False,
        "tornado_diagnosis": False,
    }
    scientific_design = {
        "world_id": WORLD_ID,
        "recipe_id": RECIPE_ID,
        "recipe_contract_version": RECIPE_CONTRACT_VERSION,
        "reference_simulation_id": REFERENCE_SIMULATION_ID,
        "controls": resolved.controls,
        "achieved_controls": resolved.achieved_controls,
        "generators": {
            "wind": "authored_true_circle_hodograph_direct_targets_v2",
            "thermodynamics": "iterated_hydrostatic_buoyancy_profile_v2",
            "initiation": "source_locked_single_thermal_v1",
        },
        "fixed_assumptions": fixed_assumptions,
    }
    identity = canonical_payload_sha256(
        {
            "scientific_design": scientific_design,
            "numerical_realization": numerical_payload,
        }
    )
    slug = _slug(request.simulation_name)
    simulation_id = f"supercells_{slug}_{identity[:8]}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"sc-{slug}-{timestamp}-{uuid4().hex[:4]}"
    existing_attempts = _existing_attempts(settings, simulation_id)
    attempt_relationship: AttemptRelationship = (
        "unchanged_retry" if existing_attempts else "initial"
    )
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise SupercellsVariationError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "sounding": package_dir / "input_sounding",
        "customization": package_dir / SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME,
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "package_report": package_dir / "supercells_variation.json",
    }
    try:
        parent_namelist = context.parent_manifest_path.parent / "namelist.input"
        if not parent_namelist.is_file():
            raise SupercellsVariationError("The selected parent namelist is unavailable.")
        paths["namelist"].write_text(
            _render_variation_namelist(parent_namelist.read_text(), resolved)
        )
        paths["sounding"].write_text(_render_input_sounding(resolved.sounding))
        init3d_path = _configured_init3d_path(settings)
        customization = supercells_source_customization_artifact(
            init3d_path.read_text(),
            initiation=resolved.initiation,
            wind_profile=[level.model_dump(mode="json") for level in resolved.hodograph],
            thermodynamic_profile=[level.model_dump(mode="json") for level in resolved.sounding],
        )
        _write_json(paths["customization"], customization)
        _write_json(
            paths["runtime_checklist"],
            {
                "status": "exact_recipe_inputs_present",
                "consumed_files": [
                    "input_sounding",
                    SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME,
                ],
                "required_files": [],
                "source_candidates": {},
            },
        )
        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key in {"namelist", "sounding", "customization", "runtime_checklist"}
        }
        package_identity = canonical_payload_sha256(
            {
                "simulation_identity_sha256": identity,
                "observation_plan": observation_payload,
                "generated_input_sha256": generated_hashes,
                "implementation_commit": implementation_commit,
            }
        )
        relationship = classify_relationship(differences)
        reference_controls = default_controls().model_dump(mode="json")
        envelope = VariationEnvelope(
            world_id=WORLD_ID,
            recipe_id=RECIPE_ID,
            recipe_contract_version=RECIPE_CONTRACT_VERSION,
            simulation_id=simulation_id,
            parent_simulation_id=request.parent_simulation_id,
            reference_simulation_id=REFERENCE_SIMULATION_ID,
            display_name=request.simulation_name.strip(),
            question=_optional_text(request.user_question),
            scientific_design=immutable_layer(scientific_design),
            numerical_realization=immutable_layer(numerical_payload),
            observation_plan=immutable_layer(observation_payload),
            world_payload={
                "controls": resolved.controls,
                "reference_controls": reference_controls,
                "parent_controls": context.parent_controls.model_dump(mode="json"),
                "requested_controls": request.controls.model_dump(mode="json"),
                "achieved_controls": resolved.achieved_controls,
                "sounding": [level.model_dump(mode="json") for level in resolved.sounding],
                "hodograph": [level.model_dump(mode="json") for level in resolved.hodograph],
                "initiation": resolved.initiation,
                "diagnostics": resolved.diagnostics.model_dump(mode="json"),
                "useful_window_end_seconds": useful_window_end_seconds,
            },
            differences=differences,
            relationship_classification=relationship,
            run_profile_id=request.run_profile_id,
            run_profile_contract=resolved.resolved_cost_profile.model_dump(mode="json"),
            cost_estimate=estimate_profile(settings, resolved.resolved_cost_profile).model_dump(
                mode="json"
            ),
            package_identity_sha256=package_identity,
            attempts=[
                *existing_attempts,
                VariationAttempt(
                    attempt_id=run_id,
                    run_id=run_id,
                    relationship=attempt_relationship,
                    package_identity_sha256=package_identity,
                    accepted_backing=False,
                ),
            ],
            validation_decisions=[
                VariationValidationDecision(
                    stage="specification",
                    disposition="passed",
                    reason=(
                        "Direct environment and initiation targets close inside "
                        "Supercells Recipe contract version 1."
                    ),
                ),
                VariationValidationDecision(
                    stage="package",
                    disposition="pending",
                    reason="Exact profile, source, namelist, and hash readback is pending.",
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
            "recipe_id": RECIPE_ID,
            "recipe_version": RUN_COST_RECIPE_VERSION,
            "profile_id": request.run_profile_id,
            "numerical_realization": numerical_payload,
            "observation_plan": observation_payload,
        }
        run_configuration: dict[str, Any] = {
            "cloud_world_id": WORLD_ID,
            "simulation_id": simulation_id,
            "simulation_display_name": request.simulation_name.strip(),
            "attempt_id": run_id,
            "attempt_relationship": attempt_relationship,
            "parent_simulation_id": request.parent_simulation_id,
            "parent_run_id": context.template.parent_run_id,
            "reference_simulation_id": REFERENCE_SIMULATION_ID,
            "user_question": _optional_text(request.user_question),
            "variation_envelope": envelope.model_dump(mode="json"),
            "configuration_difference": grouped_differences(differences),
            "warnings": resolved.warnings,
            "supercells_configuration": {
                "reference_controls": reference_controls,
                "parent_controls": context.parent_controls.model_dump(mode="json"),
                "requested_controls": request.controls.model_dump(mode="json"),
                "achieved_controls": resolved.achieved_controls,
                "sounding": [level.model_dump(mode="json") for level in resolved.sounding],
                "hodograph": [level.model_dump(mode="json") for level in resolved.hodograph],
                "initiation": resolved.initiation,
                "diagnostics": resolved.diagnostics.model_dump(mode="json"),
            },
            "duration_seconds": resolved.observation_plan.duration_seconds,
            "output_cadence_seconds": (resolved.observation_plan.output_cadence_seconds),
            "expected_model_output_count": (resolved.observation_plan.expected_history_count),
            "domain": _domain_record(paths["namelist"].read_text()),
            "generated_input_sha256": generated_hashes,
            "parent_manifest_path": str(context.parent_manifest_path),
            "cm1_provenance": provenance.report_record(),
            "cm1_source_customization_kind": (SUPERCELLS_SOURCE_CUSTOMIZATION_KIND),
            "launch_specification": launch_specification,
        }
        now = datetime.now(UTC)
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(
                id=VARIATION_CASE_ID,
                schema_version=VARIATION_SCHEMA_VERSION,
            ),
            controls=_manifest_controls(resolved.controls),
            run_configuration=run_configuration,
            physical_question=(
                _optional_text(request.user_question)
                or f"How does {request.simulation_name.strip()} differ from its parent?"
            ),
            expected_diagnostics=[
                "three_dimensional_storm_structure",
                "rotating_updraft_cloud_and_precipitation",
                "low_level_motion_and_rain_footprint",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(package_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=str(paths["sounding"]),
                dry_run_report=str(paths["package_report"]),
                cm1_source_customization=str(paths["customization"]),
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
                name=request.simulation_name.strip(),
                notes=_optional_text(request.user_question),
            ),
            pre_run_validation_report={
                "status": "passed",
                "blocking_errors": [],
                "caveats": resolved.warnings,
                "relationship_classification": relationship,
                "configuration_difference": grouped_differences(differences),
                "package_path": "shared_variation_envelope_v1",
            },
            run_recipe=RECIPE_ID,
            run_recipe_display_name=RECIPE_NAME,
            recipe_id=RECIPE_ID,
            recipe_display_name=RECIPE_NAME,
            assumption_set_id="idealized_isolated_supercell_contract_v1",
            assumption_mode="approved_recipe_contract",
            recipe_assumptions=fixed_assumptions,
            required_output_fields=list(resolved.observation_plan.retained_field_inventory),
            input_source="source_locked_generated_supercell_environment_v1",
            expected_outputs=[
                "native_numbered_cm1_model_netcdf",
                "cm1_stats_and_logs",
            ],
            run_caveats=resolved.warnings,
            manual_validation_status="approved_recipe_variation_packaged",
        )
        write_run_manifest(paths["manifest"], manifest)
        case_manifest = {
            "schema_version": VARIATION_SCHEMA_VERSION,
            "case_id": VARIATION_CASE_ID,
            "simulation_id": simulation_id,
            "parent_simulation_id": request.parent_simulation_id,
            "reference_simulation_id": REFERENCE_SIMULATION_ID,
            "recipe_id": RECIPE_ID,
            "variation_envelope_authority": {
                "manifest_path": str(paths["manifest"]),
                "run_configuration_key": "variation_envelope",
                "schema_version": envelope.schema_version,
            },
            "implementation_commit": implementation_commit,
            "run_id": run_id,
            "generated_input_sha256": generated_hashes,
            "cm1_provenance": provenance.report_record(),
        }
        _write_json(paths["case_manifest"], case_manifest)
        _write_json(
            paths["package_report"],
            {"status": "packaged_not_queued", **case_manifest},
        )
        preflight = preflight_supercells_variation(paths["manifest"])
        envelope.validation_decisions[1] = VariationValidationDecision(
            stage="package",
            disposition="passed",
            reason=(
                "Exact sounding, hodograph, thermal source, namelist, and hash readback passed."
            ),
        )
        manifest = load_run_manifest(paths["manifest"])
        run_configuration["variation_envelope"] = envelope.model_dump(mode="json")
        manifest.run_configuration = run_configuration
        manifest.updated_at = datetime.now(UTC)
        write_run_manifest(paths["manifest"], manifest)
        snapshot = create_launch_review_snapshot(
            settings,
            profile_id=request.run_profile_id,
            warning_threshold_bytes=DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
            manifest=manifest,
            resolved_profile=resolved.resolved_cost_profile,
        )
        snapshot_id = snapshot.snapshot.snapshot_id
        envelope.launch_review_snapshot_id = snapshot_id
        run_configuration["launch_review_snapshot_id"] = snapshot_id
        run_configuration["variation_envelope"] = envelope.model_dump(mode="json")
        manifest.run_configuration = run_configuration
        manifest.updated_at = datetime.now(UTC)
        write_run_manifest(paths["manifest"], manifest)
        case_manifest["launch_review_snapshot_id"] = snapshot_id
        _write_json(paths["case_manifest"], case_manifest)
        _write_json(
            paths["package_report"],
            {"status": "packaged_not_queued", **case_manifest},
        )
        return SupercellsVariationPackage(
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


def preflight_supercells_variation(manifest_path: Path) -> dict[str, Any]:
    manifest = load_run_manifest(manifest_path.expanduser())
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise SupercellsVariationError("Variation preflight requires a packaged manifest.")
    if manifest.run_configuration.get("cloud_world_id") != WORLD_ID:
        raise SupercellsVariationError("Variation manifest does not belong to Supercells.")
    envelope = _manifest_envelope(manifest)
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    required = [
        run_dir / "namelist.input",
        run_dir / "input_sounding",
        run_dir / SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME,
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
    readback = _package_readback(run_dir, envelope)
    checks = {
        "packaged_manifest": True,
        "shared_envelope": envelope.schema_version == "cloud_world_variation_v1",
        "required_inputs_present": not missing,
        "generated_hashes_match": bool(hash_checks) and all(hash_checks.values()),
        "no_existing_cm1_output": not outputs,
        "namelist_contract_matches": readback["namelist_contract_matches"],
        "sounding_profile_matches": readback["sounding_profile_matches"],
        "sounding_extends_above_model_top": readback["sounding_extends_above_model_top"],
        "source_customization_matches": readback["source_customization_matches"],
        "launch_specification_bound": isinstance(
            manifest.run_configuration.get("launch_specification"), dict
        ),
    }
    if not all(checks.values()):
        raise SupercellsVariationError(
            "Variation package preflight failed: "
            f"checks={checks}, missing={missing}, outputs={outputs}"
        )
    return {
        "passed": True,
        "checks": checks,
        "missing": missing,
        "existing_outputs": outputs,
        "generated_hash_checks": hash_checks,
        "readback": readback,
    }


def _parent_context(
    settings: CloudChamberSettings,
    parent_simulation_id: str,
) -> _ParentContext:
    parent_manifest, parent_path, display_name, source = _parent_manifest(
        settings, parent_simulation_id
    )
    parent_controls = _parent_controls(parent_simulation_id, parent_manifest)
    parent_profile_id = _parent_profile_id(parent_simulation_id, parent_manifest)
    parent_profile = profile_by_id(parent_profile_id)
    parent_numerical = parent_profile.numerical_realization.model_dump(mode="json")
    parent_observation = parent_profile.observation_plan.model_dump(mode="json")
    recipe_profiles = [
        profile
        for profile in profiles()
        if profile.world_id == WORLD_ID and profile.recipe_id == RECIPE_ID
    ]
    available_ids = {profile.profile_id for profile in recipe_profiles}
    default_profile = (
        parent_profile_id if parent_profile_id in available_ids else "supercells_standard_v1"
    )
    eligible, reason = _parent_eligibility(
        settings,
        parent_simulation_id,
        parent_manifest,
        parent_path,
    )
    template = SupercellsVariationTemplate(
        parent_simulation_id=parent_simulation_id,
        parent_run_id=parent_manifest.run_id,
        parent_display_name=display_name,
        parent_configuration_source=source,
        controls=parent_controls,
        reference_controls=default_controls(),
        run_profiles=[estimate_profile(settings, profile) for profile in recipe_profiles],
        default_run_profile_id=default_profile,
        can_create_variation=eligible,
        unavailable_reason=reason,
    )
    return _ParentContext(
        template=template,
        parent_manifest=parent_manifest,
        parent_manifest_path=parent_path,
        parent_controls=parent_controls,
        parent_numerical_realization=parent_numerical,
        parent_observation_plan=parent_observation,
    )


def _resolve_request(
    request: SupercellsVariationRequest,
    context: _ParentContext,
) -> tuple[ResolvedSupercellsRecipe, list[VariationDifference]]:
    try:
        profile = profile_by_id(request.run_profile_id)
    except ValueError as exc:
        raise SupercellsVariationError(str(exc)) from exc
    resolved = resolve_supercells_recipe(
        controls=request.controls,
        parent_controls=context.parent_controls,
        catalog_profile=profile,
    )
    differences = list(resolved.differences)
    numerical = profile.numerical_realization.model_dump(mode="json")
    observation = profile.observation_plan.model_dump(mode="json")
    if numerical != context.parent_numerical_realization:
        differences.append(
            VariationDifference(
                category="numerical_realization",
                path="numerical_realization",
                label="Numerical realization",
                before=context.parent_numerical_realization,
                after=numerical,
            )
        )
    if observation != context.parent_observation_plan:
        differences.append(
            VariationDifference(
                category="observation_plan",
                path="observation_plan",
                label="Observation plan",
                before=context.parent_observation_plan,
                after=observation,
            )
        )
    return resolved, differences


def _request_errors(
    settings: CloudChamberSettings,
    request: SupercellsVariationRequest,
    context: _ParentContext,
    resolved: ResolvedSupercellsRecipe,
    differences: list[VariationDifference],
) -> list[str]:
    errors = list(resolved.blocking_errors)
    if not context.template.can_create_variation:
        errors.append(
            context.template.unavailable_reason
            or "The selected parent cannot create another variation."
        )
    if not request.simulation_name.strip():
        errors.append("Variation name is required.")
    if not differences:
        errors.append("Change at least one scientific control or run profile before packaging.")
    if _relationship(differences) == "observation_only_attempt":
        errors.append(
            "Output-only changes are alternate_observation_attempts beneath the same "
            "Simulation; they cannot create a named Supercells Variation."
        )
    try:
        _configured_init3d_path(settings)
    except SupercellsVariationError as exc:
        errors.append(str(exc))
    return _dedupe(errors)


def _parent_manifest(
    settings: CloudChamberSettings,
    simulation_id: str,
) -> tuple[RunManifest, Path, str, str]:
    from cloud_chamber.supercells_world import supercells_world_detail

    world = supercells_world_detail(settings)
    record = next(
        (item for item in world.simulations if item.simulation_id == simulation_id),
        None,
    )
    if record is None:
        raise SupercellsVariationError(
            f"Supercells parent Simulation is unavailable: {simulation_id}."
        )
    builtins = {
        REFERENCE_SIMULATION_ID: (
            PRESENTATION_RUN_ID,
            PRESENTATION_CASE_ID,
            "Quarter-Circle Supercell",
            "Accepted Quarter-Circle presentation run",
        ),
        STRAIGHT_LINE_SIMULATION_ID: (
            STRAIGHT_LINE_PRESENTATION_RUN_ID,
            STRAIGHT_LINE_PRESENTATION_CASE_ID,
            "Straight-Line Hodograph Supercell",
            "Accepted controlled Straight-Line presentation run",
        ),
    }
    if simulation_id in builtins:
        run_id, case_id, _display_name, source = builtins[simulation_id]
        path = settings.runtime_home.expanduser() / "runs" / run_id / "run_manifest.json"
        if not path.is_file():
            raise SupercellsVariationError(
                f"The retained parent manifest is unavailable: {simulation_id}."
            )
        manifest = load_run_manifest(path)
        if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.scenario.id != case_id:
            raise SupercellsVariationError(
                f"The retained parent contract is invalid: {simulation_id}."
            )
        return manifest, path, record.display_name, source
    path = settings.runtime_home.expanduser() / "runs" / record.run_id / "run_manifest.json"
    if not path.is_file():
        raise SupercellsVariationError(
            f"The retained parent manifest is unavailable: {simulation_id}."
        )
    manifest = load_run_manifest(path)
    envelope = _manifest_envelope(manifest)
    if (
        manifest.lifecycle_state != LifecycleState.COMPLETED
        or envelope.simulation_id != simulation_id
    ):
        raise SupercellsVariationError(f"The retained parent contract is invalid: {simulation_id}.")
    return (
        manifest,
        path,
        record.display_name,
        "Current accepted descendant resolved from the Supercells World inventory",
    )


def _parent_controls(
    simulation_id: str,
    manifest: RunManifest,
) -> SupercellsControls:
    if simulation_id == REFERENCE_SIMULATION_ID:
        return default_controls()
    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        return default_controls().model_copy(update={"hodograph_family": "straight"})
    envelope = _manifest_envelope(manifest)
    controls = envelope.world_payload.get("controls")
    if not isinstance(controls, dict):
        raise SupercellsVariationError("The selected parent is missing exact Supercells controls.")
    return normalize_controls(SupercellsControls.model_validate(controls))


def _parent_profile_id(simulation_id: str, manifest: RunManifest) -> str:
    if simulation_id in {REFERENCE_SIMULATION_ID, STRAIGHT_LINE_SIMULATION_ID}:
        return "supercells_presentation_v1"
    return _manifest_envelope(manifest).run_profile_id


def _parent_eligibility(
    settings: CloudChamberSettings,
    simulation_id: str,
    manifest: RunManifest,
    manifest_path: Path,
) -> tuple[bool, str | None]:
    from cloud_chamber.supercells_world import validate_supercells_parent_eligibility

    if manifest.lifecycle_state != LifecycleState.COMPLETED:
        return False, "The selected parent is not complete."
    if not (manifest_path.parent / "namelist.input").is_file():
        return False, "The selected parent namelist is unavailable."
    eligible, reason = validate_supercells_parent_eligibility(
        settings,
        simulation_id=simulation_id,
        manifest=manifest,
        manifest_path=manifest_path,
    )
    return (True, None) if eligible else (False, reason)


def _render_variation_namelist(
    parent_text: str,
    resolved: ResolvedSupercellsRecipe,
) -> str:
    numerical = resolved.resolved_cost_profile.numerical_realization.exact_domain
    duration = resolved.observation_plan.duration_seconds
    cadence = resolved.observation_plan.output_cadence_seconds
    if numerical is None or duration is None or cadence is None:
        raise SupercellsVariationError("Resolved run profile is incomplete.")
    replacements = {
        "nx": str(numerical.nx),
        "ny": str(numerical.ny),
        "nz": str(numerical.nz),
        "dx": f"{numerical.dx_m:g}",
        "dy": f"{numerical.dy_m:g}",
        "dz": f"{numerical.dz_m:.10g}",
        "dtl": f"{numerical.timestep_seconds:g}",
        "timax": f"{duration:g}",
        "tapfrq": f"{cadence:g}",
        "iinit": "1",
        "isnd": "7",
        "iwnd": "0",
        "imoist": "1",
        "ptype": "5",
        "zd": "15000",
        "ztop": f"{numerical.model_top_m:g}",
        "stretch_z": "0",
        "umove": f"{resolved.diagnostics.model_translation_u_m_s:.8f}",
        "vmove": f"{resolved.diagnostics.model_translation_v_m_s:.8f}",
        "output_format": "2",
        "output_filetype": "2",
        "output_rain": "1",
        "output_th": "1",
        "output_prs": "1",
        "output_qv": "1",
        "output_q": "1",
        "output_dbz": "1",
        "output_uinterp": "1",
        "output_vinterp": "1",
        "output_winterp": "1",
        "output_vort": "1",
        "output_uh": "1",
    }
    assignments = parse_namelist_assignments(parent_text)
    missing = sorted(set(replacements) - set(assignments))
    if missing:
        raise SupercellsVariationError(f"Parent namelist lacks required assignments: {missing}")
    rendered = parent_text
    for name, value in replacements.items():
        if parse_namelist_assignments(rendered)[name] != value:
            rendered = replace_namelist_assignment(rendered, name, value)
    return rendered


def _render_input_sounding(levels: list[SupercellsProfileLevel]) -> str:
    surface = levels[0]
    lines = [f"{surface.pressure_pa / 100.0:.6f} {surface.theta_k:.9f} {surface.qv_g_kg:.9f}"]
    for level in levels:
        lines.append(
            f"{level.height_m:.3f} {level.theta_k:.9f} {level.qv_g_kg:.9f} "
            f"{level.u_m_s:.9f} {level.v_m_s:.9f}"
        )
    return "\n".join(lines) + "\n"


def _package_readback(
    run_dir: Path,
    envelope: VariationEnvelope,
) -> dict[str, Any]:
    namelist = parse_namelist_assignments((run_dir / "namelist.input").read_text())
    numerical = envelope.run_profile_contract["numerical_realization"]["exact_domain"]
    observation = envelope.observation_plan.payload
    expected_namelist = {
        "nx": int(numerical["nx"]),
        "ny": int(numerical["ny"]),
        "nz": int(numerical["nz"]),
        "dx": float(numerical["dx_m"]),
        "dy": float(numerical["dy_m"]),
        "dz": float(numerical["dz_m"]),
        "dtl": float(numerical["timestep_seconds"]),
        "timax": float(observation["duration_seconds"]),
        "tapfrq": float(observation["output_cadence_seconds"]),
        "isnd": 7,
        "iwnd": 0,
        "iinit": 1,
        "ptype": 5,
    }
    namelist_matches = all(
        math.isclose(float(namelist[key]), float(value), rel_tol=0.0, abs_tol=1.0e-6)
        for key, value in expected_namelist.items()
    )
    expected_sounding = envelope.world_payload["sounding"]
    actual_sounding = _read_input_sounding(run_dir / "input_sounding")
    sounding_matches = len(actual_sounding) == len(expected_sounding) and all(
        all(
            math.isclose(
                float(actual[key]),
                float(expected[key]),
                rel_tol=0.0,
                abs_tol=2.0e-6,
            )
            for key in ("height_m", "theta_k", "qv_g_kg", "u_m_s", "v_m_s")
        )
        for actual, expected in zip(
            actual_sounding,
            expected_sounding,
            strict=True,
        )
    )
    customization = load_supercells_source_customization(
        run_dir / SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME
    )
    initiation = envelope.world_payload["initiation"]
    source_matches = customization["initiation"] == {
        key: initiation[key]
        for key in (
            "amplitude_k",
            "horizontal_radius_m",
            "vertical_radius_m",
            "center_height_m_agl",
            "center_x_m",
            "center_y_m",
        )
    }
    return {
        "namelist_contract_matches": namelist_matches,
        "sounding_profile_matches": sounding_matches,
        "source_customization_matches": source_matches,
        "sounding_level_count": len(actual_sounding),
        "sounding_top_m": actual_sounding[-1]["height_m"],
        "model_top_m": numerical["model_top_m"],
        "sounding_extends_above_model_top": (
            actual_sounding[-1]["height_m"] > numerical["model_top_m"]
        ),
    }


def _read_input_sounding(path: Path) -> list[dict[str, float]]:
    rows = [
        [float(value) for value in line.split()]
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    if len(rows) < 4 or len(rows[0]) != 3:
        raise SupercellsVariationError("Generated input_sounding is malformed.")
    profile = rows[1:]
    if any(len(row) != 5 for row in profile):
        raise SupercellsVariationError("Generated input_sounding profile row is malformed.")
    return [
        {
            "height_m": row[0],
            "theta_k": row[1],
            "qv_g_kg": row[2],
            "u_m_s": row[3],
            "v_m_s": row[4],
        }
        for row in profile
    ]


def _configured_init3d_path(settings: CloudChamberSettings) -> Path:
    if settings.cm1_root is None:
        raise SupercellsVariationError(
            "Supercells packaging requires a configured CM1 source root."
        )
    path = settings.cm1_root.expanduser() / "src" / "init3d.F"
    if not path.is_file():
        raise SupercellsVariationError("Configured CM1 source root is missing src/init3d.F.")
    return path


def _manifest_envelope(manifest: RunManifest) -> VariationEnvelope:
    payload = manifest.run_configuration.get("variation_envelope")
    if not isinstance(payload, dict):
        raise SupercellsVariationError(
            "Supercells variation manifest is missing its shared envelope."
        )
    try:
        envelope = VariationEnvelope.model_validate(payload)
    except ValueError as exc:
        raise SupercellsVariationError(f"Supercells variation envelope is invalid: {exc}") from exc
    if envelope.world_id != WORLD_ID or envelope.recipe_id != RECIPE_ID:
        raise SupercellsVariationError(
            "Variation envelope does not belong to the approved Supercells Recipe."
        )
    return envelope


def _existing_attempts(
    settings: CloudChamberSettings,
    simulation_id: str,
) -> list[VariationAttempt]:
    attempts: dict[str, VariationAttempt] = {}
    run_root = settings.runtime_home.expanduser() / "runs"
    for path in run_root.glob("*/run_manifest.json"):
        try:
            envelope = _manifest_envelope(load_run_manifest(path))
        except (OSError, RunManifestError, SupercellsVariationError):
            continue
        if envelope.simulation_id != simulation_id:
            continue
        for attempt in envelope.attempts:
            attempts[attempt.run_id] = attempt
    return sorted(attempts.values(), key=lambda attempt: attempt.run_id)


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


def _relationship(differences: list[VariationDifference]) -> str | None:
    try:
        return classify_relationship(differences)
    except ValueError:
        return None


def _useful_window_end_seconds(profile_id: str, duration_seconds: int) -> int:
    if duration_seconds <= 0:
        raise SupercellsVariationError(
            f"Supercells run profile has no declared duration: {profile_id}."
        )
    return min(duration_seconds, 10_800)


def _manifest_controls(
    controls: dict[str, Any],
) -> dict[str, str | float | bool]:
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


__all__ = [
    "SupercellsVariationError",
    "SupercellsVariationPackage",
    "SupercellsVariationPreview",
    "SupercellsVariationRequest",
    "SupercellsVariationTemplate",
    "create_supercells_variation",
    "preflight_supercells_variation",
    "preview_supercells_variation",
    "supercells_variation_template",
]
