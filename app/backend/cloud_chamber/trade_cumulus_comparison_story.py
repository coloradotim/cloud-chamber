"""Curated Trade Cumulus moisture-comparison story."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Literal, NoReturn, cast

from pydantic import BaseModel, ConfigDict, ValidationError

from cloud_chamber.result_ingest import (
    ResultIngestError,
    ResultMetadata,
)
from cloud_chamber.result_ingest import (
    get_result_metadata as get_result_metadata,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_moisture_comparison import (
    PairedScalarMetric,
    TimedValue,
    TradeCumulusPairedEvidence,
    TradeCumulusRunEvidence,
)
from cloud_chamber.trade_cumulus_updraft_lens import (
    CLOUD_THRESHOLD_KG_KG,
    TRADE_CUMULUS_UPDRAFT_SCALE_BREAKPOINTS_M_S,
    TRADE_CUMULUS_UPDRAFT_SCALE_COLORS,
    TRADE_CUMULUS_UPDRAFT_SCALE_ID,
    TradeCumulusUpdraftLensDefaults,
    TradeCumulusUpdraftLensError,
    TradeCumulusUpdraftLensFrame,
    trade_cumulus_updraft_lens_defaults,
    trade_cumulus_updraft_lens_frame,
)

COMPARISON_ID: Literal["trade_cumulus_moisture_v1"] = "trade_cumulus_moisture_v1"
COMPARISON_GROUP_ID: Literal["trade_cumulus_moisture_v1"] = "trade_cumulus_moisture_v1"
PRODUCT_SLICE_ID: Literal["trade_cumulus_v1"] = "trade_cumulus_v1"
CASE_ID: Literal["bomex_trade_cumulus_baseline_v0"] = "bomex_trade_cumulus_baseline_v0"
BASELINE_RESULT_ID = "result-trade-cumulus-presentation-v1-baseline-20260722"
MORE_MOISTURE_RESULT_ID = "result-trade-cumulus-presentation-v1-more-moisture-20260722"
BASELINE_RUN_ID = "trade-cumulus-presentation-v1-baseline-20260722"
MORE_MOISTURE_RUN_ID = "trade-cumulus-presentation-v1-more-moisture-20260722"
EXPECTED_FIXED_ASSUMPTIONS_SHA256 = (
    "861375a82d209c36cc63ccce2d20934553b0e7e8811579c718dfb275899172a7"
)
EXPECTED_IMPLEMENTATION_COMMIT = "4647ef54a6c1b7a5d31e6e758c3c276fc5e5b2e0"
EXPECTED_CM1_SOURCE_MANIFEST_SHA256 = (
    "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
)
EXPECTED_CM1_EXECUTABLE_SHA256 = "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
COMPARISON_EVIDENCE_RELATIVE_PATH = (
    "comparisons/trade-cumulus-presentation-v1-20260722/comparison_evidence.json"
)
COMPARISON_EVIDENCE_VERSION = "trade_cumulus_moisture_comparison_evidence_v2"
RUN_EVIDENCE_VERSION = "trade_cumulus_moisture_run_evidence_v1"
FINAL_THREE_HOUR_START_SECONDS = 3_600.0


class TradeCumulusComparisonStoryNotFound(RuntimeError):
    """Raised when an approved comparison artifact is unavailable."""


class TradeCumulusComparisonStoryConflict(RuntimeError):
    """Raised when runtime evidence contradicts the approved comparison."""


class CuratedView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_index: int
    time_seconds: float
    orientation: Literal["vertical_x"]
    plane_dimension: Literal["y"]
    plane_index: int
    plane_coordinate: float
    plane_units: Literal["km"]
    camera_preset: Literal["overview"]
    cloud_field: Literal["ql"]
    cloud_threshold_kg_kg: float
    lens_id: Literal["updraft"]
    scale_id: Literal["trade_cumulus_updraft_velocity_v1"]
    wind_mode: Literal["perturbation"]
    show_wind: Literal[True]
    show_cloud_boundary: Literal[True]
    opacity: float
    point_size: int
    caption: str


class ComparisonMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    display_name: str
    control_state: Literal["baseline", "more_moisture"]
    control_label: Literal["Surface moisture supply"]
    control_value: float
    control_units: Literal["g/g m/s"]
    control_display: str
    curated_view: CuratedView


class ChangedCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Literal["Surface moisture supply"]
    baseline_display: str
    more_moisture_display: str
    change_display: Literal["+50%"]


class MaterialResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    label: str
    baseline_value: float
    more_moisture_value: float
    absolute_delta: float
    percent_delta: float
    units: str
    method: str
    window: str
    baseline_display: str
    more_moisture_display: str
    change_display: str


class AuthoredResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str


class HeldFixedGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str


class HeldFixedByDesign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead: Literal["Only surface moisture supply changed."]
    groups: list[HeldFixedGroup]


class EvidenceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_window: Literal["time >= 3600 s"]
    analysis_start_seconds: float
    analysis_end_seconds: float
    output_cadence_seconds: int
    paired_saved_frame_count: int


class ComparisonProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_state: Literal["matched_runs_valid"]
    evidence_version: str
    implementation_commit: str
    fixed_assumptions_sha256: str
    baseline_run_id: str
    baseline_result_id: str
    more_moisture_run_id: str
    more_moisture_result_id: str
    scale_id: Literal["trade_cumulus_updraft_velocity_v1"]
    comparison_source: Literal["runtime_matched_pair_evidence"]


class TradeCumulusComparisonStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison_id: Literal["trade_cumulus_moisture_v1"]
    comparison_group_id: Literal["trade_cumulus_moisture_v1"]
    product_slice_id: Literal["trade_cumulus_v1"]
    case_id: Literal["bomex_trade_cumulus_baseline_v0"]
    title: str
    question: str
    illustrative_view_note: str
    baseline: ComparisonMember
    more_moisture: ComparisonMember
    changed_condition: ChangedCondition
    material_responses: list[MaterialResponse]
    small_or_mixed_responses: list[AuthoredResponse]
    held_fixed_by_design: HeldFixedByDesign
    explanation_paragraphs: list[str]
    evidence_summary: EvidenceSummary
    provenance: ComparisonProvenance
    caveats: list[str]


@dataclass(frozen=True)
class _CuratedViewSpec:
    result_id: str
    time_index: int
    time_seconds: float
    plane_index: int
    plane_coordinate: float
    caption: str


@dataclass(frozen=True)
class _MetricSpec:
    key: str
    units: str
    method: str
    window: str
    baseline: float
    more_moisture: float
    absolute_delta: float
    percent_delta: float


BASELINE_VIEW = _CuratedViewSpec(
    result_id=BASELINE_RESULT_ID,
    time_index=201,
    time_seconds=12_060.0,
    plane_index=83,
    plane_coordinate=2.366666555404663,
    caption=(
        "This illustrative Baseline view shows several active cells across the slice, with "
        "rising cores bordered by sinking air."
    ),
)
MORE_MOISTURE_VIEW = _CuratedViewSpec(
    result_id=MORE_MOISTURE_RESULT_ID,
    time_index=232,
    time_seconds=13_920.0,
    plane_index=72,
    plane_coordinate=1.6333333253860474,
    caption=(
        "This illustrative More Moisture view shows a concentrated active core within a "
        "broader region of cloud and vertical motion."
    ),
)

_METRIC_SPECS = {
    "mean_total_cloud_cover_final_three_hours": _MetricSpec(
        key="mean_total_cloud_cover_final_three_hours",
        units="%",
        method="time mean of horizontal columns containing ql >= 1e-6 kg/kg",
        window="time >= 3600 s",
        baseline=12.049246566144873,
        more_moisture=14.248040880141192,
        absolute_delta=2.198794313996318,
        percent_delta=18.24839671033321,
    ),
    "domain_mean_cwp_final_three_hour_mean": _MetricSpec(
        key="domain_mean_cwp_final_three_hour_mean",
        units="kg/m^2",
        method="time mean of horizontal domain-mean cwp",
        window="time >= 3600 s",
        baseline=0.006739830541318102,
        more_moisture=0.009686668911071296,
        absolute_delta=0.0029468383697531936,
        percent_delta=43.72273682087092,
    ),
    "coherent_cloud_top_final_three_hour_mean": _MetricSpec(
        key="coherent_cloud_top_final_three_hour_mean",
        units="m",
        method="mean supported coherent cloud-object top",
        window="time >= 3600 s",
        baseline=1750.690681499671,
        more_moisture=1859.9172027071536,
        absolute_delta=109.22652120748262,
        percent_delta=6.2390530983987045,
    ),
    "first_isolated_cloud_liquid_time": _MetricSpec(
        key="first_isolated_cloud_liquid_time",
        units="s",
        method="first model frame with any finite ql >= 1e-6 kg/kg",
        window="full run",
        baseline=1140.0,
        more_moisture=1140.0,
        absolute_delta=0.0,
        percent_delta=0.0,
    ),
    "time_mean_cloud_fraction_profile_peak_height": _MetricSpec(
        key="time_mean_cloud_fraction_profile_peak_height",
        units="m",
        method="height of first maximum in final-three-hour time-mean cloud-fraction profile",
        window="time >= 3600 s",
        baseline=615.0000095367432,
        more_moisture=585.0000381469727,
        absolute_delta=-29.999971389770508,
        percent_delta=-4.87804405277463,
    ),
    "cloudy_scalar_cells_with_positive_centered_w": _MetricSpec(
        key="cloudy_scalar_cells_with_positive_centered_w",
        units="%",
        method="pooled fraction of cloudy scalar cells with centered w > 0",
        window="time >= 3600 s",
        baseline=89.51790219011582,
        more_moisture=89.54264215595985,
        absolute_delta=0.024739965844034373,
        percent_delta=0.02763689188280158,
    ),
}


def trade_cumulus_moisture_comparison_story(
    settings: CloudChamberSettings,
) -> TradeCumulusComparisonStory:
    """Return the one approved, evidence-backed Trade Cumulus comparison story."""
    evidence = _load_and_validate_evidence(settings)
    baseline_metadata = _load_result(settings, BASELINE_RESULT_ID)
    more_metadata = _load_result(settings, MORE_MOISTURE_RESULT_ID)
    _validate_result_metadata(
        baseline_metadata,
        evidence.baseline,
        result_id=BASELINE_RESULT_ID,
        run_id=BASELINE_RUN_ID,
        control_state="baseline",
        control_value=5.2e-5,
    )
    _validate_result_metadata(
        more_metadata,
        evidence.more_moisture,
        result_id=MORE_MOISTURE_RESULT_ID,
        run_id=MORE_MOISTURE_RUN_ID,
        control_state="more_moisture",
        control_value=7.8e-5,
    )
    _validate_shared_cm1_provenance(baseline_metadata, more_metadata)
    baseline_view = _validated_curated_view(settings, BASELINE_VIEW)
    more_view = _validated_curated_view(settings, MORE_MOISTURE_VIEW)
    metrics = {key: _validated_metric(evidence, spec) for key, spec in _METRIC_SPECS.items()}
    paired_frame_count = _validate_mixed_time_series(evidence)

    return TradeCumulusComparisonStory(
        comparison_id=COMPARISON_ID,
        comparison_group_id=COMPARISON_GROUP_ID,
        product_slice_id=PRODUCT_SLICE_ID,
        case_id=CASE_ID,
        title="Trade Cumulus: Baseline and More Moisture",
        question="How does stronger surface moisture supply change the trade-cumulus field?",
        illustrative_view_note=(
            "Illustrative views: selected to help show the response measured across the full "
            "simulations. Times and locations may differ, and these are not corresponding "
            "individual clouds."
        ),
        baseline=_member(
            evidence.baseline,
            baseline_view,
            display_name="Canonical BOMEX Baseline",
            control_display="0.0520 g/kg m/s",
        ),
        more_moisture=_member(
            evidence.more_moisture,
            more_view,
            display_name="More Moisture",
            control_display="0.0780 g/kg m/s",
        ),
        changed_condition=ChangedCondition(
            label="Surface moisture supply",
            baseline_display="0.0520 g/kg m/s",
            more_moisture_display="0.0780 g/kg m/s",
            change_display="+50%",
        ),
        material_responses=[
            _material_response(
                metrics["mean_total_cloud_cover_final_three_hours"],
                metric_id="mean_cloud_cover_final_three_hours",
                label="Mean cloud cover, final three hours",
                baseline_display="12.049%",
                more_display="14.248%",
                change_display="+2.199 percentage points",
            ),
            _material_response(
                metrics["domain_mean_cwp_final_three_hour_mean"],
                metric_id="mean_cloud_water_path_final_three_hours",
                label="Mean cloud-water path, final three hours",
                baseline_display="0.006740 kg/m²",
                more_display="0.009687 kg/m²",
                change_display="+43.723%",
            ),
            _material_response(
                metrics["coherent_cloud_top_final_three_hour_mean"],
                metric_id="mean_coherent_cloud_top_final_three_hours",
                label="Mean coherent cloud top, final three hours",
                baseline_display="1,751 m",
                more_display="1,860 m",
                change_display="+109 m",
            ),
        ],
        small_or_mixed_responses=[
            AuthoredResponse(
                title="Initial cloud-liquid onset was unchanged.",
                body="Both simulations first reached the cloud-liquid threshold at 1,140 s.",
            ),
            AuthoredResponse(
                title="The cloud-fraction peak shifted only slightly.",
                body=(
                    "The final-three-hour profile peaked near 615 m in Baseline and 585 m in "
                    "More Moisture."
                ),
            ),
            AuthoredResponse(
                title="The fraction of cloudy air rising changed very little.",
                body="It was 89.518% in Baseline and 89.543% in More Moisture.",
            ),
            AuthoredResponse(
                title="The response varied through time.",
                body=(
                    "More Moisture was not cloudier or wetter than Baseline at every individual "
                    "saved frame."
                ),
            ),
        ],
        held_fixed_by_design=HeldFixedByDesign(
            lead="Only surface moisture supply changed.",
            groups=[
                HeldFixedGroup(
                    title="Initial atmosphere",
                    body=(
                        "Thermodynamic, moisture, and wind profiles, including the deterministic "
                        "perturbation."
                    ),
                ),
                HeldFixedGroup(
                    title="Forcing",
                    body=(
                        "Sensible heat supply, friction velocity, large-scale forcing, "
                        "geostrophic wind, and Coriolis treatment."
                    ),
                ),
                HeldFixedGroup(
                    title="Model setup",
                    body=(
                        "Moist physics, turbulence, boundaries, domain, grid, and timestep "
                        "strategy."
                    ),
                ),
                HeldFixedGroup(
                    title="Execution and outputs",
                    body=(
                        "Duration, output cadence, requested fields, CM1 source and executable, "
                        "and the Cloud Chamber implementation commit."
                    ),
                ),
            ],
        ),
        explanation_paragraphs=[
            (
                "More surface moisture produced a cloudier, wetter, somewhat deeper "
                "trade-cumulus field."
            ),
            (
                "Only the lower-boundary moisture supply changed. Over the final three hours, "
                "More Moisture covered more of the domain with cloud, held about 43 percent more "
                "mean cloud-water path, and produced coherent clouds averaging 109 meters taller."
            ),
            (
                "It did not create a completely different circulation regime. Initial "
                "cloud-liquid onset was unchanged, the cloud-fraction maximum shifted only 30 "
                "meters lower, and about 89.5 percent of cloudy cells were rising in both "
                "simulations."
            ),
            (
                "The illustrative Lens views are selected to help show the measured response. "
                "They show different times and locations and are not one-to-one matches of "
                "individual clouds. More Moisture was also not cloudier at every saved frame, so "
                "the result is a change in the evolving cloud field rather than a rule that every "
                "moment must look larger."
            ),
        ],
        evidence_summary=EvidenceSummary(
            analysis_window="time >= 3600 s",
            analysis_start_seconds=FINAL_THREE_HOUR_START_SECONDS,
            analysis_end_seconds=float(evidence.baseline.duration_seconds),
            output_cadence_seconds=evidence.baseline.output_cadence_seconds,
            paired_saved_frame_count=paired_frame_count,
        ),
        provenance=ComparisonProvenance(
            evidence_state="matched_runs_valid",
            evidence_version=evidence.evidence_version,
            implementation_commit=evidence.implementation_commit,
            fixed_assumptions_sha256=EXPECTED_FIXED_ASSUMPTIONS_SHA256,
            baseline_run_id=evidence.baseline.run_id,
            baseline_result_id=evidence.baseline.result_id,
            more_moisture_run_id=evidence.more_moisture.run_id,
            more_moisture_result_id=evidence.more_moisture.result_id,
            scale_id=cast(
                Literal["trade_cumulus_updraft_velocity_v1"],
                TRADE_CUMULUS_UPDRAFT_SCALE_ID,
            ),
            comparison_source="runtime_matched_pair_evidence",
        ),
        caveats=[
            "one_deterministic_les_realization_per_control_state",
            "illustrative_views_are_not_direct_frame_matches",
            "individual_clouds_are_not_paired_one_to_one",
            "candidate_product_slice_not_supported_status",
        ],
    )


def _load_and_validate_evidence(settings: CloudChamberSettings) -> TradeCumulusPairedEvidence:
    path = settings.runtime_home.expanduser() / COMPARISON_EVIDENCE_RELATIVE_PATH
    if not path.is_file():
        raise TradeCumulusComparisonStoryNotFound("Comparison evidence is unavailable.")
    try:
        payload = json.loads(path.read_text())
        evidence = TradeCumulusPairedEvidence.model_validate(payload)
    except OSError as exc:
        raise TradeCumulusComparisonStoryNotFound("Comparison evidence is unavailable.") from exc
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
        raise TradeCumulusComparisonStoryConflict(
            "Comparison evidence does not match the required schema."
        ) from exc

    _require_equal(evidence.evidence_version, COMPARISON_EVIDENCE_VERSION, "evidence version")
    _require_equal(evidence.evidence_state, "matched_runs_valid", "evidence state")
    _require_equal(
        evidence.implementation_commit,
        EXPECTED_IMPLEMENTATION_COMMIT,
        "implementation commit",
    )
    _validate_evidence_member(
        evidence.baseline,
        result_id=BASELINE_RESULT_ID,
        run_id=BASELINE_RUN_ID,
        control_state="baseline",
        control_value=5.2e-5,
        implementation_commit=evidence.implementation_commit,
    )
    _validate_evidence_member(
        evidence.more_moisture,
        result_id=MORE_MOISTURE_RESULT_ID,
        run_id=MORE_MOISTURE_RUN_ID,
        control_state="more_moisture",
        control_value=7.8e-5,
        implementation_commit=evidence.implementation_commit,
    )
    proof = evidence.matched_package_proof
    if not proof.valid:
        _conflict("matched package proof")
    _require_equal(
        proof.baseline_run_id,
        BASELINE_RUN_ID,
        "matched package Baseline identity",
    )
    _require_equal(
        proof.more_moisture_run_id,
        MORE_MOISTURE_RUN_ID,
        "matched package More Moisture identity",
    )
    _require_equal(
        proof.differing_namelist_assignments,
        ["cnst_lhflx"],
        "matched package changed assignments",
    )
    _require_equal(
        proof.fixed_assumptions_sha256,
        EXPECTED_FIXED_ASSUMPTIONS_SHA256,
        "matched package fixed assumptions hash",
    )
    if evidence.stage4_consistency is not None and not evidence.stage4_consistency.passed:
        _conflict("historical Stage 4 consistency")
    return evidence


def _validate_evidence_member(
    member: TradeCumulusRunEvidence,
    *,
    result_id: str,
    run_id: str,
    control_state: str,
    control_value: float,
    implementation_commit: str,
) -> None:
    expected = {
        "run evidence version": (member.evidence_version, RUN_EVIDENCE_VERSION),
        "product slice": (member.product_slice_id, PRODUCT_SLICE_ID),
        "comparison group": (member.comparison_group_id, COMPARISON_GROUP_ID),
        "case identity": (member.case_id, CASE_ID),
        "control identity": (member.control_id, "surface_moisture_supply"),
        "control state": (member.control_state, control_state),
        "run length": (member.run_length, "full"),
        "run identity": (member.run_id, run_id),
        "result identity": (member.result_id, result_id),
        "run implementation commit": (member.app_commit, EXPECTED_IMPLEMENTATION_COMMIT),
        "run/top-level implementation commit": (member.app_commit, implementation_commit),
        "run lifecycle": (member.gate.lifecycle_state, "completed"),
        "run product state": (member.gate.product_state, "completed_cm1_result"),
    }
    for label, (actual, wanted) in expected.items():
        _require_equal(actual, wanted, label)
    _require_exact_float(member.surface_moisture_flux_g_g_m_s, control_value, "surface moisture")
    _require_exact_float(
        member.gate.intended_surface_moisture_flux_g_g_m_s,
        control_value,
        "gated surface moisture",
    )
    if not member.gate.valid or member.gate.failures:
        _conflict("run gate")


def _load_result(settings: CloudChamberSettings, result_id: str) -> ResultMetadata:
    try:
        return get_result_metadata(settings, result_id)
    except (ResultIngestError, OSError) as exc:
        raise TradeCumulusComparisonStoryNotFound(
            "An approved comparison result is unavailable."
        ) from exc


def _validate_result_metadata(
    metadata: ResultMetadata,
    evidence: TradeCumulusRunEvidence,
    *,
    result_id: str,
    run_id: str,
    control_state: str,
    control_value: float,
) -> None:
    controls = metadata.controls
    configuration = metadata.run_configuration
    expected = {
        "persisted result identity": (metadata.result_id, result_id),
        "persisted run identity": (metadata.run_id, run_id),
        "persisted scenario identity": (metadata.scenario_id, CASE_ID),
        "persisted lifecycle": (metadata.source_lifecycle_state, "completed"),
        "persisted product state": (metadata.source_product_state, "completed_cm1_result"),
        "persisted case identity": (configuration.get("case_id"), CASE_ID),
        "persisted product slice": (configuration.get("product_slice_id"), PRODUCT_SLICE_ID),
        "persisted comparison group": (
            configuration.get("comparison_group_id"),
            COMPARISON_GROUP_ID,
        ),
        "persisted control identity": (controls.get("control_id"), "surface_moisture_supply"),
        "persisted control state": (controls.get("control_state"), control_state),
        "configured control identity": (
            configuration.get("control_id"),
            "surface_moisture_supply",
        ),
        "configured control state": (configuration.get("control_state"), control_state),
        "result/evidence run identity": (metadata.run_id, evidence.run_id),
    }
    for label, (actual, wanted) in expected.items():
        _require_equal(actual, wanted, label)
    _require_exact_float(
        controls.get("surface_moisture_flux_g_g_m_s"), control_value, "control value"
    )
    _require_exact_float(
        configuration.get("surface_moisture_flux_g_g_m_s"),
        control_value,
        "configured control value",
    )
    _require_equal(
        configuration.get("fixed_assumptions_sha256"),
        EXPECTED_FIXED_ASSUMPTIONS_SHA256,
        "fixed assumptions hash",
    )


def _validate_shared_cm1_provenance(
    baseline: ResultMetadata,
    more_moisture: ResultMetadata,
) -> None:
    baseline_source, baseline_executable = _cm1_provenance_hashes(baseline, "Baseline")
    more_source, more_executable = _cm1_provenance_hashes(more_moisture, "More Moisture")
    _require_equal(baseline_source, more_source, "paired CM1 source manifest hash")
    _require_equal(baseline_executable, more_executable, "paired CM1 executable hash")
    _require_equal(
        baseline_source,
        EXPECTED_CM1_SOURCE_MANIFEST_SHA256,
        "Baseline CM1 source manifest hash",
    )
    _require_equal(
        more_source,
        EXPECTED_CM1_SOURCE_MANIFEST_SHA256,
        "More Moisture CM1 source manifest hash",
    )
    _require_equal(
        baseline_executable,
        EXPECTED_CM1_EXECUTABLE_SHA256,
        "Baseline CM1 executable hash",
    )
    _require_equal(
        more_executable,
        EXPECTED_CM1_EXECUTABLE_SHA256,
        "More Moisture CM1 executable hash",
    )


def _cm1_provenance_hashes(metadata: ResultMetadata, member_label: str) -> tuple[str, str]:
    provenance = metadata.run_configuration.get("cm1_provenance")
    if not isinstance(provenance, dict):
        _conflict(f"{member_label} CM1 provenance")
    source_hash = provenance.get("source_manifest_sha256")
    executable_hash = provenance.get("executable_sha256")
    if not isinstance(source_hash, str) or not source_hash:
        _conflict(f"{member_label} CM1 source manifest hash")
    if not isinstance(executable_hash, str) or not executable_hash:
        _conflict(f"{member_label} CM1 executable hash")
    return source_hash, executable_hash


def _validated_curated_view(
    settings: CloudChamberSettings,
    spec: _CuratedViewSpec,
) -> CuratedView:
    try:
        defaults = trade_cumulus_updraft_lens_defaults(settings, spec.result_id)
        _validate_scale(defaults)
        frame = trade_cumulus_updraft_lens_frame(
            settings,
            spec.result_id,
            time_index=spec.time_index,
            orientation="vertical_x",
            plane_index=spec.plane_index,
            wind_mode="perturbation",
        )
    except (ResultIngestError, OSError) as exc:
        raise TradeCumulusComparisonStoryNotFound(
            "A curated comparison view artifact is unavailable."
        ) from exc
    except TradeCumulusUpdraftLensError as exc:
        message = str(exc).lower()
        if "unavailable" in message or "no readable" in message or "no netcdf" in message:
            raise TradeCumulusComparisonStoryNotFound(
                "A curated comparison view artifact is unavailable."
            ) from exc
        raise TradeCumulusComparisonStoryConflict(
            "A curated comparison view could not be reproduced."
        ) from exc
    _validate_frame(frame, spec)
    return CuratedView(
        time_index=spec.time_index,
        time_seconds=spec.time_seconds,
        orientation="vertical_x",
        plane_dimension="y",
        plane_index=spec.plane_index,
        plane_coordinate=spec.plane_coordinate,
        plane_units="km",
        camera_preset="overview",
        cloud_field="ql",
        cloud_threshold_kg_kg=CLOUD_THRESHOLD_KG_KG,
        lens_id="updraft",
        scale_id=cast(
            Literal["trade_cumulus_updraft_velocity_v1"],
            TRADE_CUMULUS_UPDRAFT_SCALE_ID,
        ),
        wind_mode="perturbation",
        show_wind=True,
        show_cloud_boundary=True,
        opacity=0.68,
        point_size=11,
        caption=spec.caption,
    )


def _validate_scale(
    scale: TradeCumulusUpdraftLensDefaults | TradeCumulusUpdraftLensFrame,
) -> None:
    _require_equal(scale.w_scale_id, TRADE_CUMULUS_UPDRAFT_SCALE_ID, "updraft scale")
    _require_equal(
        scale.w_scale_breakpoints_m_s,
        list(TRADE_CUMULUS_UPDRAFT_SCALE_BREAKPOINTS_M_S),
        "updraft scale breakpoints",
    )
    _require_equal(
        scale.w_scale_colors,
        list(TRADE_CUMULUS_UPDRAFT_SCALE_COLORS),
        "updraft scale colors",
    )
    _require_exact_float(
        scale.cloud_threshold_kg_kg,
        CLOUD_THRESHOLD_KG_KG,
        "cloud threshold",
    )


def _validate_frame(frame: TradeCumulusUpdraftLensFrame, spec: _CuratedViewSpec) -> None:
    _validate_scale(frame)
    expected = {
        "curated result": (frame.result_id, spec.result_id),
        "curated time index": (frame.time_index, spec.time_index),
        "curated orientation": (frame.orientation, "vertical_x"),
        "curated plane dimension": (frame.plane_dimension, "y"),
        "curated plane index": (frame.plane_index, spec.plane_index),
        "curated plane units": (frame.plane_units, "km"),
        "curated wind mode": (frame.wind_mode, "perturbation"),
    }
    for label, (actual, wanted) in expected.items():
        _require_equal(actual, wanted, label)
    _require_exact_float(frame.time_seconds, spec.time_seconds, "curated time")
    _require_close(
        frame.plane_coordinate,
        spec.plane_coordinate,
        "curated plane coordinate",
        abs_tol=1e-9,
    )
    if frame.w_finite_count <= 0:
        _conflict("curated vertical velocity")
    if not any(any(row) for row in frame.cloud_mask):
        _conflict("curated cloud boundary")
    if not frame.wind_vectors:
        _conflict("curated wind vectors")


def _validated_metric(
    evidence: TradeCumulusPairedEvidence,
    spec: _MetricSpec,
) -> PairedScalarMetric:
    metric = evidence.scalar_metrics.get(spec.key)
    if metric is None:
        _conflict(f"metric {spec.key}")
    assert metric is not None
    _require_equal(metric.units, spec.units, f"metric {spec.key} units")
    _require_equal(metric.method, spec.method, f"metric {spec.key} method")
    _require_equal(metric.window, spec.window, f"metric {spec.key} window")
    _require_equal(metric.quality, "trusted", f"metric {spec.key} quality")
    _require_close(metric.baseline, spec.baseline, f"metric {spec.key} Baseline")
    _require_close(
        metric.more_moisture,
        spec.more_moisture,
        f"metric {spec.key} More Moisture",
    )
    _require_close(metric.absolute_delta, spec.absolute_delta, f"metric {spec.key} delta")
    _require_close(metric.percent_delta, spec.percent_delta, f"metric {spec.key} percent delta")
    return metric


def _validate_mixed_time_series(evidence: TradeCumulusPairedEvidence) -> int:
    counts = []
    for key in ("domain_mean_cwp", "total_cloud_cover_percent"):
        baseline = evidence.baseline.time_series.get(key)
        more = evidence.more_moisture.time_series.get(key)
        paired = evidence.exact_time_pairing.get(key)
        if baseline is None or more is None or paired is None:
            _conflict(f"exact-time {key}")
        assert baseline is not None and more is not None and paired is not None
        _validate_paired_series(key, baseline, more, paired)
        counts.append(len(paired))
    if counts[0] != counts[1]:
        _conflict("exact-time pairing length")
    return counts[0]


def _validate_paired_series(
    key: str,
    baseline: list[TimedValue],
    more: list[TimedValue],
    paired: list[TimedValue],
) -> None:
    if not baseline or len(baseline) != len(more) or len(baseline) != len(paired):
        _conflict(f"exact-time {key} length")
    has_not_greater = False
    for baseline_value, more_value, paired_value in zip(baseline, more, paired, strict=True):
        _require_exact_float(
            more_value.time_seconds,
            baseline_value.time_seconds,
            f"exact-time {key} member time",
        )
        _require_exact_float(
            paired_value.time_seconds,
            baseline_value.time_seconds,
            f"exact-time {key} paired time",
        )
        if baseline_value.value is None or more_value.value is None:
            if paired_value.value is not None:
                _conflict(f"exact-time {key} unavailable value")
            continue
        expected_delta = more_value.value - baseline_value.value
        _require_close(paired_value.value, expected_delta, f"exact-time {key} delta")
        if more_value.value <= baseline_value.value:
            has_not_greater = True
    if not has_not_greater:
        _conflict(f"exact-time {key} mixed response")


def _member(
    evidence: TradeCumulusRunEvidence,
    view: CuratedView,
    *,
    display_name: str,
    control_display: str,
) -> ComparisonMember:
    return ComparisonMember(
        result_id=evidence.result_id,
        run_id=evidence.run_id,
        display_name=display_name,
        control_state=cast(Literal["baseline", "more_moisture"], evidence.control_state),
        control_label="Surface moisture supply",
        control_value=evidence.surface_moisture_flux_g_g_m_s,
        control_units="g/g m/s",
        control_display=control_display,
        curated_view=view,
    )


def _material_response(
    metric: PairedScalarMetric,
    *,
    metric_id: str,
    label: str,
    baseline_display: str,
    more_display: str,
    change_display: str,
) -> MaterialResponse:
    if (
        metric.baseline is None
        or metric.more_moisture is None
        or metric.absolute_delta is None
        or metric.percent_delta is None
    ):
        _conflict(f"material response {metric_id}")
    return MaterialResponse(
        metric_id=metric_id,
        label=label,
        baseline_value=metric.baseline,
        more_moisture_value=metric.more_moisture,
        absolute_delta=metric.absolute_delta,
        percent_delta=metric.percent_delta,
        units=metric.units,
        method=metric.method,
        window=metric.window,
        baseline_display=baseline_display,
        more_moisture_display=more_display,
        change_display=change_display,
    )


def _require_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        _conflict(label)


def _require_exact_float(actual: object, expected: float, label: str) -> None:
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        _conflict(label)
    if float(actual) != expected:
        _conflict(label)


def _require_close(
    actual: float | None,
    expected: float,
    label: str,
    *,
    abs_tol: float = 1e-12,
) -> None:
    if actual is None or not math.isfinite(actual):
        _conflict(label)
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=abs_tol):
        _conflict(label)


def _conflict(label: str) -> NoReturn:
    raise TradeCumulusComparisonStoryConflict(
        f"Comparison evidence conflicts with the approved {label}."
    )
