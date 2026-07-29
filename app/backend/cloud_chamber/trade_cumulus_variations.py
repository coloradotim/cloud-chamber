"""Durable Trade Cumulus variation envelopes and deterministic packaging."""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from cloud_chamber import __version__
from cloud_chamber.bomex_case import (
    CASE_ID,
    BomexVariant,
    collect_cm1_provenance,
    render_bomex_namelist,
    replace_bomex_namelist_assignment,
    sha256_file,
    verified_clean_git_commit,
)
from cloud_chamber.cloud_worlds import (
    MORE_MOISTURE_SIMULATION_ID,
    REFERENCE_SIMULATION_ID,
    SimulationRecord,
    trade_cumulus_world_detail,
)
from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
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
from cloud_chamber.trade_cumulus_forcing import (
    TRADE_CUMULUS_FORCING_ARTIFACT_FILENAME,
    TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
    TRADE_CUMULUS_FORCING_TARGET,
    forcing_customization_artifact,
    verify_forcing_artifact,
)
from cloud_chamber.trade_cumulus_recipes import (
    RECIPE_CONTRACT_VERSION,
    RECIPE_ID,
    RECIPE_NAME,
    RUN_COST_RECIPE_VERSION,
    ResolvedTradeCumulusRecipe,
    TradeCumulusControls,
    default_controls,
    normalize_controls,
    resolve_trade_cumulus_recipe,
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

WORLD_ID = "trade_cumulus"
VARIATION_CASE_ID = "trade_cumulus_recipe_variation_v1"
VARIATION_SCHEMA_VERSION = "trade_cumulus_variation_v1"
DEFAULT_PROFILE_ID = "trade_cumulus_standard_v1"


class TradeCumulusVariationError(RuntimeError):
    """Raised when an approved Trade Cumulus variation cannot be represented honestly."""


class TradeCumulusVariationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str = REFERENCE_SIMULATION_ID
    simulation_name: str
    user_question: str | None = None
    recipe_id: str = RECIPE_ID
    run_profile_id: str = DEFAULT_PROFILE_ID
    controls: TradeCumulusControls


class TradeCumulusVariationTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_simulation_id: str
    parent_run_id: str
    parent_display_name: str
    parent_configuration_source: str
    reference_simulation_id: str = REFERENCE_SIMULATION_ID
    recipe_id: str = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    recipe_contract_version: str = RECIPE_CONTRACT_VERSION
    controls: TradeCumulusControls
    canonical_reference_controls: TradeCumulusControls
    run_profiles: list[RunCostEstimate]
    default_run_profile_id: str
    can_create_variation: bool
    unavailable_reason: str | None = None


class TradeCumulusVariationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    requested_controls: dict[str, float]
    resolved_controls: dict[str, float | None]
    canonical_reference_controls: dict[str, float]
    parent_controls: dict[str, float]
    differences: dict[str, list[dict[str, Any]]]
    relationship_classification: str | None
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: dict[str, Any]
    sounding_profile: list[dict[str, Any]]
    forcing_profile: list[dict[str, Any]]
    numerical_realization: dict[str, Any]
    observation_plan: dict[str, Any]
    cost_estimate: RunCostEstimate
    source_customization_required: bool


class TradeCumulusVariationPackage(BaseModel):
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

    template: TradeCumulusVariationTemplate
    parent: SimulationRecord
    parent_manifest: RunManifest
    parent_manifest_path: Path
    parent_controls: TradeCumulusControls
    parent_profile_id: str
    parent_numerical_realization: dict[str, Any]
    parent_observation_plan: dict[str, Any]


def trade_cumulus_variation_template(
    settings: CloudChamberSettings,
    parent_simulation_id: str,
) -> TradeCumulusVariationTemplate:
    return _variation_context(settings, parent_simulation_id).template


def preview_trade_cumulus_variation(
    settings: CloudChamberSettings,
    request: TradeCumulusVariationRequest,
) -> TradeCumulusVariationPreview:
    context = _variation_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(request, context)
    errors = _request_errors(request, context, resolved, differences)
    return TradeCumulusVariationPreview(
        requested_controls=normalize_controls(request.controls).model_dump(mode="json"),
        resolved_controls={
            key: value if math.isfinite(value) else None
            for key, value in resolved.achieved_controls.items()
        },
        canonical_reference_controls=default_controls().model_dump(mode="json"),
        parent_controls=context.parent_controls.model_dump(mode="json"),
        differences=grouped_differences(differences),
        relationship_classification=_relationship(differences),
        warnings=_dedupe(resolved.warnings),
        blocking_errors=_dedupe(errors),
        diagnostics=resolved.diagnostics.model_dump(mode="json"),
        sounding_profile=[level.model_dump(mode="json") for level in resolved.sounding],
        forcing_profile=[level.model_dump(mode="json") for level in resolved.forcing_profile],
        numerical_realization=resolved.resolved_cost_profile.numerical_realization.model_dump(
            mode="json"
        ),
        observation_plan=resolved.observation_plan.model_dump(mode="json"),
        cost_estimate=estimate_profile(settings, resolved.resolved_cost_profile),
        source_customization_required=_forcing_changed(normalize_controls(request.controls)),
    )


def create_trade_cumulus_variation(
    settings: CloudChamberSettings,
    request: TradeCumulusVariationRequest,
) -> TradeCumulusVariationPackage:
    context = _variation_context(settings, request.parent_simulation_id)
    resolved, differences = _resolve_request(request, context)
    errors = _request_errors(request, context, resolved, differences)
    if errors:
        raise TradeCumulusVariationError(" ".join(_dedupe(errors)))
    implementation_commit = verified_clean_git_commit()
    provenance = collect_cm1_provenance(settings)
    controls = normalize_controls(request.controls)
    numerical_payload = resolved.resolved_cost_profile.numerical_realization.model_dump(mode="json")
    observation_payload = resolved.observation_plan.model_dump(mode="json")
    scientific_design: dict[str, Any] = {
        "world_id": WORLD_ID,
        "recipe_id": RECIPE_ID,
        "recipe_contract_version": RECIPE_CONTRACT_VERSION,
        "reference_simulation_id": REFERENCE_SIMULATION_ID,
        "controls": controls.model_dump(mode="json"),
        "achieved_controls": resolved.achieved_controls,
        "fixed_assumptions": {
            "case_family": "BOMEX shallow cumulus",
            "microphysics": "reversible moist thermodynamics without precipitation fallout",
            "surface_forcing": "spatially uniform signed kinematic fluxes",
            "large_scale_profile_shapes": "canonical BOMEX piecewise profiles",
            "initial_profile_path": "consumed external CM1 isnd=7 sounding",
        },
    }
    identity = canonical_payload_sha256(
        {
            "scientific_design": scientific_design,
            "numerical_realization": numerical_payload,
        }
    )
    slug = _slug(request.simulation_name)
    simulation_id = f"trade_cumulus_{slug}_{identity[:8]}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"tc-{slug}-{timestamp}-{uuid4().hex[:4]}"
    existing_attempts = _existing_attempts(settings, simulation_id)
    attempt_relationship: AttemptRelationship = (
        "unchanged_retry" if existing_attempts else "initial"
    )
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise TradeCumulusVariationError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "sounding": package_dir / "input_sounding",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "package_report": package_dir / "trade_cumulus_variation.json",
    }
    forcing_changed = _forcing_changed(controls)
    if forcing_changed:
        paths["forcing_customization"] = package_dir / TRADE_CUMULUS_FORCING_ARTIFACT_FILENAME
    try:
        reference_namelist = Path(provenance.bundled_bomex_namelist_path).read_text()
        namelist = _render_namelist(reference_namelist, controls, request.run_profile_id)
        paths["namelist"].write_text(namelist)
        paths["sounding"].write_text(_render_sounding(resolved))
        if forcing_changed:
            source = (Path(provenance.source_tree_path) / TRADE_CUMULUS_FORCING_TARGET).read_text()
            _write_json(
                paths["forcing_customization"],
                forcing_customization_artifact(
                    source,
                    vertical_motion_m_s=controls.large_scale_vertical_motion_m_s,
                    temperature_tendency_k_day=controls.temperature_tendency_k_day,
                    total_water_tendency_g_kg_day=controls.total_water_tendency_g_kg_day,
                ),
            )
        _write_json(
            paths["runtime_checklist"],
            {
                "status": (
                    "external_sounding_and_source_locked_forcing_customization"
                    if forcing_changed
                    else "external_sounding_with_canonical_source_forcing"
                ),
                "consumed_files": ["input_sounding"],
                "required_files": ["LANDUSE.TBL"],
                "source_candidates": {
                    "LANDUSE.TBL": ["config_files/les_ShallowCu/LANDUSE.TBL", "LANDUSE.TBL"]
                },
                "packaged_source_customization": (
                    TRADE_CUMULUS_FORCING_ARTIFACT_FILENAME if forcing_changed else None
                ),
            },
        )
        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key
            in {
                "namelist",
                "sounding",
                "runtime_checklist",
                "forcing_customization",
            }
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
        cost_estimate = estimate_profile(settings, resolved.resolved_cost_profile)
        envelope = VariationEnvelope(
            world_id=WORLD_ID,
            recipe_id=RECIPE_ID,
            recipe_contract_version=RECIPE_CONTRACT_VERSION,
            simulation_id=simulation_id,
            parent_simulation_id=context.parent.simulation_id or request.parent_simulation_id,
            reference_simulation_id=REFERENCE_SIMULATION_ID,
            display_name=request.simulation_name.strip(),
            question=_optional_text(request.user_question),
            scientific_design=immutable_layer(scientific_design),
            numerical_realization=immutable_layer(numerical_payload),
            observation_plan=immutable_layer(observation_payload),
            world_payload={
                "controls": controls.model_dump(mode="json"),
                "achieved_controls": resolved.achieved_controls,
                "sounding": [level.model_dump(mode="json") for level in resolved.sounding],
                "forcing_profile": [
                    level.model_dump(mode="json") for level in resolved.forcing_profile
                ],
                "diagnostics": resolved.diagnostics.model_dump(mode="json"),
            },
            differences=differences,
            relationship_classification=relationship,
            run_profile_id=request.run_profile_id,
            run_profile_contract=resolved.resolved_cost_profile.model_dump(mode="json"),
            cost_estimate=cost_estimate.model_dump(mode="json"),
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
                        "Requested physical targets were generated within declared tolerances."
                    ),
                ),
                VariationValidationDecision(
                    stage="package",
                    disposition="pending",
                    reason="Exact generated-input hashes await package preflight.",
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
            "parent_simulation_id": context.parent.simulation_id,
            "parent_run_id": context.parent.run_id,
            "parent_result_id": context.parent.result_id,
            "reference_simulation_id": REFERENCE_SIMULATION_ID,
            "reference_result_id": (
                trade_cumulus_world_detail(settings).reference_simulation.result_id
            ),
            "source_recipe_id": RECIPE_ID,
            "user_question": _optional_text(request.user_question),
            "case_id": CASE_ID,
            "variation_envelope": envelope.model_dump(mode="json"),
            "trade_cumulus_configuration": {
                "controls": controls.model_dump(mode="json"),
                "achieved_controls": resolved.achieved_controls,
                "duration_seconds": resolved.observation_plan.duration_seconds,
                "output_cadence_seconds": resolved.observation_plan.output_cadence_seconds,
            },
            "configuration_difference": grouped_differences(differences),
            "warnings": resolved.warnings,
            "duration_seconds": resolved.observation_plan.duration_seconds,
            "output_cadence_seconds": resolved.observation_plan.output_cadence_seconds,
            "expected_model_output_count": resolved.observation_plan.expected_history_count,
            "domain": _domain_record(request.run_profile_id),
            "generated_input_sha256": generated_hashes,
            "parent_manifest_path": str(context.parent_manifest_path),
            "cm1_provenance": provenance.model_dump(mode="json"),
            "launch_specification": launch_specification,
            "cm1_source_customization_kind": (
                TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND if forcing_changed else None
            ),
        }
        now = datetime.now(UTC)
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(
                id=VARIATION_CASE_ID,
                schema_version=VARIATION_SCHEMA_VERSION,
            ),
            controls={
                key: value
                for key, value in controls.model_dump(mode="json").items()
                if isinstance(value, str | float | int | bool)
            },
            run_configuration=run_configuration,
            physical_question=(
                _optional_text(request.user_question)
                or f"How does {request.simulation_name.strip()} differ from its parent?"
            ),
            expected_diagnostics=[
                "cloud_liquid_and_cloud_fraction",
                "vertical_velocity_and_horizontal_wind",
                "domain_mean_thermodynamic_profiles",
                "surface_and_large_scale_forcing",
                "runtime_integrity_and_non_finite_scan",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(package_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=str(paths["sounding"]),
                dry_run_report=str(paths["package_report"]),
                cm1_source_customization=(
                    str(paths["forcing_customization"]) if forcing_changed else None
                ),
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
                "target_achievement": resolved.achieved_controls,
                "package_path": "shared_variation_envelope_v1",
            },
            run_recipe=RECIPE_ID,
            run_recipe_display_name=RECIPE_NAME,
            recipe_id=RECIPE_ID,
            recipe_display_name=RECIPE_NAME,
            assumption_set_id=f"{RECIPE_ID}_contract_v1",
            assumption_mode="approved_recipe_contract",
            recipe_assumptions=scientific_design["fixed_assumptions"],
            required_output_fields=list(resolved.observation_plan.retained_field_inventory),
            input_source="source_locked_bomex_external_profile_transform_v1",
            expected_outputs=["native_numbered_cm1_model_netcdf", "cm1_stats_and_logs"],
            run_caveats=resolved.warnings,
            manual_validation_status="approved_recipe_variation_packaged",
        )
        write_run_manifest(paths["manifest"], manifest)
        case_manifest: dict[str, Any] = {
            "schema_version": VARIATION_SCHEMA_VERSION,
            "variation_envelope_authority": {
                "manifest_path": str(paths["manifest"]),
                "run_configuration_key": "variation_envelope",
                "schema_version": envelope.schema_version,
            },
            "implementation_commit": implementation_commit,
            "run_id": run_id,
            "generated_input_sha256": generated_hashes,
            "target_achievement": resolved.achieved_controls,
            "cm1_provenance": provenance.model_dump(mode="json"),
        }
        _write_json(paths["case_manifest"], case_manifest)
        _write_json(paths["package_report"], {"status": "packaged_not_queued", **case_manifest})
        preflight = preflight_trade_cumulus_variation(paths["manifest"])
        envelope.validation_decisions[1] = VariationValidationDecision(
            stage="package",
            disposition="passed",
            reason="Exact generated-input hashes and package preflight passed.",
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
        _write_json(paths["package_report"], {"status": "packaged_not_queued", **case_manifest})
        return TradeCumulusVariationPackage(
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


def preflight_trade_cumulus_variation(manifest_path: Path) -> dict[str, Any]:
    manifest = load_run_manifest(manifest_path.expanduser())
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise TradeCumulusVariationError("Variation preflight requires a packaged manifest.")
    if manifest.run_configuration.get("cloud_world_id") != WORLD_ID:
        raise TradeCumulusVariationError("Variation manifest does not belong to Trade Cumulus.")
    envelope = _manifest_envelope(manifest)
    try:
        controls = normalize_controls(
            TradeCumulusControls.model_validate(envelope.world_payload.get("controls"))
        )
        profile = profile_by_id(envelope.run_profile_id)
        resolved = resolve_trade_cumulus_recipe(
            controls=controls,
            parent_controls=controls,
            catalog_profile=profile,
        )
    except (ValueError, TypeError) as exc:
        raise TradeCumulusVariationError(
            "Variation package does not resolve through the declared Recipe contract."
        ) from exc
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    required = [
        run_dir / "namelist.input",
        run_dir / "input_sounding",
        run_dir / "runtime_file_checklist.json",
        run_dir / "case_manifest.json",
    ]
    customization = manifest.generated_inputs.cm1_source_customization
    if customization:
        required.append(Path(customization).expanduser())
    missing = [path.name for path in required if not path.is_file()]
    outputs = sorted(path.name for path in run_dir.glob("cm1out*") if path.is_file())
    try:
        verified_hashes = verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError:
        verified_hashes = {}
    source_customization_valid = True
    if customization:
        provenance = manifest.run_configuration.get("cm1_provenance")
        source_root = (
            Path(str(provenance.get("source_tree_path")))
            if isinstance(provenance, dict)
            else Path()
        )
        source_path = source_root / TRADE_CUMULUS_FORCING_TARGET
        try:
            verify_forcing_artifact(Path(customization), source_path.read_text())
        except (OSError, ValueError):
            source_customization_valid = False
    namelist_text = (run_dir / "namelist.input").read_text()
    sounding_text = (run_dir / "input_sounding").read_text()
    expected_namelist = {
        **_PROFILE_REALIZATIONS[envelope.run_profile_id],
        "isnd": 7,
        "iwnd": 0,
        "cnst_shflx": controls.surface_sensible_heat_flux_k_m_s,
        "cnst_lhflx": controls.surface_moisture_flux_g_kg_m_s / 1_000.0,
    }
    namelist_readback = {name: _namelist_number(namelist_text, name) for name in expected_namelist}
    namelist_matches = all(
        value is not None
        and math.isclose(
            value,
            float(expected),
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        )
        for (name, expected), value in zip(
            expected_namelist.items(), namelist_readback.values(), strict=True
        )
    )
    expected_observation = resolved.observation_plan.model_dump(mode="json")
    declared_observation = envelope.observation_plan.payload
    declared_domain = manifest.run_configuration.get("domain")
    expected_domain = _domain_record(envelope.run_profile_id)
    checks = {
        "packaged_manifest": True,
        "shared_envelope": envelope.schema_version == "cloud_world_variation_v1",
        "required_inputs_present": not missing,
        "generated_hashes_match": bool(verified_hashes),
        "no_existing_cm1_output": not outputs,
        "external_sounding_consumed": namelist_readback["isnd"] == 7,
        "namelist_matches_reviewed_contract": namelist_matches,
        "sounding_matches_reviewed_contract": sounding_text == _render_sounding(resolved),
        "achieved_targets_match_review": envelope.world_payload.get("achieved_controls")
        == resolved.achieved_controls,
        "observation_plan_matches_review": declared_observation == expected_observation,
        "domain_matches_review": declared_domain == expected_domain,
        "required_fields_match_review": manifest.required_output_fields
        == list(resolved.observation_plan.retained_field_inventory),
        "expected_histories_match_review": manifest.run_configuration.get(
            "expected_model_output_count"
        )
        == resolved.observation_plan.expected_history_count,
        "source_customization_valid": source_customization_valid,
        "launch_specification_bound": isinstance(
            manifest.run_configuration.get("launch_specification"), dict
        ),
    }
    if not all(checks.values()):
        raise TradeCumulusVariationError(
            "Variation package preflight failed: "
            f"checks={checks}, missing={missing}, outputs={outputs}"
        )
    return {
        "passed": True,
        "checks": checks,
        "missing": missing,
        "existing_outputs": outputs,
        "generated_hash_checks": {key: True for key in verified_hashes},
        "namelist_readback": namelist_readback,
    }


def _variation_context(
    settings: CloudChamberSettings,
    parent_simulation_id: str,
) -> _VariationContext:
    world = trade_cumulus_world_detail(settings)
    parent = next(
        (
            simulation
            for simulation in world.simulations
            if simulation.simulation_id == parent_simulation_id
        ),
        None,
    )
    if parent is None:
        raise ValueError(f"Trade Cumulus Simulation {parent_simulation_id} was not found.")
    manifest_path = (
        settings.runtime_home.expanduser() / "runs" / parent.run_id / "run_manifest.json"
    )
    if not manifest_path.is_file():
        raise TradeCumulusVariationError("The selected parent manifest is unavailable.")
    manifest = load_run_manifest(manifest_path)
    parent_controls = _parent_controls(parent, manifest)
    parent_profile_id = _parent_profile_id(parent, manifest)
    recipe_profiles = [
        profile
        for profile in profiles()
        if profile.world_id == WORLD_ID and profile.recipe_id == RECIPE_ID
    ]
    estimates = [estimate_profile(settings, profile) for profile in recipe_profiles]
    parent_profile = profile_by_id(parent_profile_id)
    parent_resolved = resolve_trade_cumulus_recipe(
        controls=parent_controls,
        parent_controls=parent_controls,
        catalog_profile=parent_profile,
    )
    parent_numerical, parent_observation = _parent_layers(
        manifest,
        parent_resolved.resolved_cost_profile.numerical_realization.model_dump(mode="json"),
        parent_resolved.observation_plan.model_dump(mode="json"),
    )
    can_create, unavailable_reason = _parent_eligibility(parent, manifest)
    template = TradeCumulusVariationTemplate(
        parent_simulation_id=parent.simulation_id or parent_simulation_id,
        parent_run_id=parent.run_id,
        parent_display_name=parent.display_name,
        parent_configuration_source=(
            "retained Recipe controls resolved against the canonical BOMEX reference"
            if parent.role == "variation"
            and parent.simulation_id
            not in {
                MORE_MOISTURE_SIMULATION_ID,
            }
            else "retained canonical BOMEX source-backed atmosphere and forcing"
        ),
        controls=parent_controls,
        canonical_reference_controls=default_controls(),
        run_profiles=estimates,
        default_run_profile_id=(
            parent_profile_id
            if parent_profile_id in {profile.profile_id for profile in recipe_profiles}
            else DEFAULT_PROFILE_ID
        ),
        can_create_variation=can_create,
        unavailable_reason=unavailable_reason,
    )
    return _VariationContext(
        template=template,
        parent=parent,
        parent_manifest=manifest,
        parent_manifest_path=manifest_path,
        parent_controls=parent_controls,
        parent_profile_id=parent_profile_id,
        parent_numerical_realization=parent_numerical,
        parent_observation_plan=parent_observation,
    )


def _resolve_request(
    request: TradeCumulusVariationRequest,
    context: _VariationContext,
) -> tuple[ResolvedTradeCumulusRecipe, list[VariationDifference]]:
    if request.recipe_id != RECIPE_ID:
        raise TradeCumulusVariationError("The selected parent and Recipe do not match.")
    try:
        profile = profile_by_id(request.run_profile_id)
    except ValueError as exc:
        raise TradeCumulusVariationError(str(exc)) from exc
    resolved = resolve_trade_cumulus_recipe(
        controls=request.controls,
        parent_controls=context.parent_controls,
        catalog_profile=profile,
    )
    differences = list(resolved.differences)
    numerical = resolved.resolved_cost_profile.numerical_realization.model_dump(mode="json")
    observation = resolved.observation_plan.model_dump(mode="json")
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
    request: TradeCumulusVariationRequest,
    context: _VariationContext,
    resolved: ResolvedTradeCumulusRecipe,
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
    material = [
        difference
        for difference in differences
        if difference.material and difference.category != "observation_plan"
    ]
    if not material:
        if any(difference.category == "observation_plan" for difference in differences):
            errors.append(
                "Changing only the observation plan creates another attempt beneath the "
                "same Simulation, not a new Variation."
            )
        else:
            errors.append("Change at least one effective Recipe or numerical control.")
    return errors


def _parent_controls(
    parent: SimulationRecord,
    manifest: RunManifest,
) -> TradeCumulusControls:
    payload = manifest.run_configuration.get("variation_envelope")
    if isinstance(payload, dict):
        world_payload = payload.get("world_payload")
        if isinstance(world_payload, dict) and isinstance(world_payload.get("controls"), dict):
            try:
                return normalize_controls(
                    TradeCumulusControls.model_validate(world_payload["controls"])
                )
            except ValueError:
                pass
    controls = default_controls().model_dump(mode="json")
    if parent.simulation_id == MORE_MOISTURE_SIMULATION_ID:
        controls["surface_moisture_flux_g_kg_m_s"] = 0.078
    return TradeCumulusControls.model_validate(controls)


def _parent_profile_id(parent: SimulationRecord, manifest: RunManifest) -> str:
    payload = manifest.run_configuration.get("variation_envelope")
    if isinstance(payload, dict) and isinstance(payload.get("run_profile_id"), str):
        return str(payload["run_profile_id"])
    if "presentation" in parent.run_id:
        return "trade_cumulus_presentation_v1"
    return "trade_cumulus_full_cycle_v1"


def _parent_layers(
    manifest: RunManifest,
    fallback_numerical: dict[str, Any],
    fallback_observation: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        envelope = _manifest_envelope(manifest)
    except TradeCumulusVariationError:
        return fallback_numerical, fallback_observation
    return envelope.numerical_realization.payload, envelope.observation_plan.payload


def _parent_eligibility(
    parent: SimulationRecord,
    manifest: RunManifest,
) -> tuple[bool, str | None]:
    if parent.technical_state != "available" or not parent.explore_available:
        return False, "Only an available, inspectable Simulation can parent a variation."
    if parent.simulation_id in {REFERENCE_SIMULATION_ID, MORE_MOISTURE_SIMULATION_ID}:
        return True, None
    try:
        envelope = _manifest_envelope(manifest)
    except TradeCumulusVariationError:
        return (
            False,
            "This inspectable Simulation predates the shared Recipe envelope and cannot "
            "parent a new variation.",
        )
    if not envelope.parent_eligible:
        return False, envelope.parent_eligibility_reason
    return True, None


def _manifest_envelope(manifest: RunManifest) -> VariationEnvelope:
    payload = manifest.run_configuration.get("variation_envelope")
    if not isinstance(payload, dict):
        raise TradeCumulusVariationError("This variation predates the shared Recipe envelope.")
    try:
        envelope = VariationEnvelope.model_validate(payload)
    except ValueError as exc:
        raise TradeCumulusVariationError("Variation envelope is invalid.") from exc
    if envelope.world_id != WORLD_ID or envelope.recipe_id != RECIPE_ID:
        raise TradeCumulusVariationError("Variation envelope has the wrong World or Recipe.")
    return envelope


def _existing_attempts(
    settings: CloudChamberSettings,
    simulation_id: str,
) -> list[VariationAttempt]:
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if not runs_dir.exists():
        return []
    attempts: dict[str, tuple[str, VariationAttempt]] = {}
    for manifest_path in runs_dir.glob("*/run_manifest.json"):
        try:
            manifest = load_run_manifest(manifest_path)
        except (OSError, ValueError):
            continue
        if (
            manifest.run_configuration.get("cloud_world_id") != WORLD_ID
            or manifest.run_configuration.get("simulation_id") != simulation_id
        ):
            continue
        envelope = _manifest_envelope(manifest)
        declared = next(
            (attempt for attempt in envelope.attempts if attempt.run_id == manifest.run_id),
            None,
        )
        if declared is not None:
            attempts[manifest.run_id] = (manifest.created_at.isoformat(), declared)
    ordered = [attempt for _created, attempt in sorted(attempts.values())]
    accepted = [attempt for attempt in ordered if attempt.accepted_backing]
    if len(accepted) > 1:
        raise TradeCumulusVariationError(
            "Existing attempts contain conflicting accepted-backing claims."
        )
    return ordered


def _render_namelist(
    reference_text: str,
    controls: TradeCumulusControls,
    profile_id: str,
) -> str:
    profile = _PROFILE_REALIZATIONS[profile_id]
    rendered = render_bomex_namelist(reference_text, BomexVariant.FULL)
    replacements = {
        **{key: str(value) for key, value in profile.items()},
        "isnd": "7",
        "iwnd": "0",
        "cnst_shflx": _scientific(controls.surface_sensible_heat_flux_k_m_s),
        "cnst_lhflx": _scientific(controls.surface_moisture_flux_g_kg_m_s / 1_000.0),
    }
    for name, value in replacements.items():
        rendered = replace_bomex_namelist_assignment(rendered, name, value)
    return rendered.rstrip() + "\n"


def _render_sounding(resolved: ResolvedTradeCumulusRecipe) -> str:
    surface = resolved.sounding[0]
    lines = [
        f"{surface.pressure_pa / 100.0:.4f} {surface.theta_l_k:.6f} {surface.total_water_g_kg:.9f}"
    ]
    lines.extend(
        f"{level.height_m:.1f} {level.theta_l_k:.6f} "
        f"{level.total_water_g_kg:.9f} {level.u_m_s:.6f} {level.v_m_s:.6f}"
        for level in resolved.sounding
    )
    return "\n".join(lines) + "\n"


def _forcing_changed(controls: TradeCumulusControls) -> bool:
    reference = default_controls()
    return any(
        not math.isclose(getattr(controls, field), getattr(reference, field), abs_tol=1.0e-12)
        for field in (
            "large_scale_vertical_motion_m_s",
            "temperature_tendency_k_day",
            "total_water_tendency_g_kg_day",
        )
    )


def _domain_record(profile_id: str) -> dict[str, float]:
    exact = profile_by_id(profile_id).numerical_realization.exact_domain
    if exact is None:
        raise TradeCumulusVariationError(
            "Trade Cumulus run profile lacks an exact numerical realization."
        )
    return {
        key: float(value)
        for key, value in exact.model_dump(mode="json").items()
        if key != "timestep_seconds"
    }


def _namelist_assignment(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*([^,!/]+)", text)
    return match.group(1).strip() if match else None


def _namelist_number(text: str, name: str) -> float | None:
    value = _namelist_assignment(text, name)
    if value is None:
        return None
    try:
        return float(value.replace("d", "e").replace("D", "E"))
    except ValueError:
        return None


def _relationship(differences: list[VariationDifference]) -> str | None:
    try:
        return classify_relationship(differences)
    except ValueError:
        return None


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:48] or "variation"


def _optional_text(value: str | None) -> str | None:
    stripped = value.strip() if value else ""
    return stripped or None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _scientific(value: float) -> str:
    if value == 0.0:
        return "0.0"
    return f"{value:.12e}"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


_PROFILE_REALIZATIONS: dict[str, dict[str, int | float]] = {
    "trade_cumulus_quick_v1": {
        "nx": 64,
        "ny": 64,
        "nz": 75,
        "dx": 100,
        "dy": 100,
        "dz": 40,
        "dtl": 3,
        "timax": 10_800,
        "tapfrq": 180,
    },
    "trade_cumulus_standard_v1": {
        "nx": 64,
        "ny": 64,
        "nz": 75,
        "dx": 100,
        "dy": 100,
        "dz": 40,
        "dtl": 3,
        "timax": 14_400,
        "tapfrq": 120,
    },
    "trade_cumulus_full_cycle_v1": {
        "nx": 64,
        "ny": 64,
        "nz": 75,
        "dx": 100,
        "dy": 100,
        "dz": 40,
        "dtl": 3,
        "timax": 21_600,
        "tapfrq": 120,
    },
    "trade_cumulus_presentation_v1": {
        "nx": 96,
        "ny": 96,
        "nz": 100,
        "dx": 66.66666667,
        "dy": 66.66666667,
        "dz": 30,
        "dtl": 2,
        "timax": 14_400,
        "tapfrq": 60,
    },
    "trade_cumulus_extended_v1": {
        "nx": 128,
        "ny": 128,
        "nz": 75,
        "dx": 100,
        "dy": 100,
        "dz": 40,
        "dtl": 3,
        "timax": 14_400,
        "tapfrq": 120,
    },
}
