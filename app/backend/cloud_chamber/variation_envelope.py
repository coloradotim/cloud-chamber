"""Shared durable identity and relationship contract for Cloud World variations."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VARIATION_ENVELOPE_SCHEMA_VERSION: Literal["cloud_world_variation_v1"] = "cloud_world_variation_v1"

DifferenceCategory = Literal[
    "terrain",
    "wind",
    "moisture",
    "stability_thermodynamics",
    "forcing_initiation",
    "numerical_realization",
    "observation_plan",
]
RelationshipClassification = Literal[
    "controlled_physical_variation",
    "controlled_initiation_sensitivity",
    "multi_factor_physical_variation",
    "numerical_sensitivity",
    "mixed_variation",
    "replicate_realization",
    "observation_only_attempt",
]
AttemptRelationship = Literal[
    "initial",
    "unchanged_retry",
    "checkpoint_restart",
    "alternate_observation_attempt",
    "extension",
    "later_backing_candidate",
]
AvailabilityState = Literal[
    "intended",
    "packaged",
    "queued",
    "running",
    "available",
    "available_with_caveats",
    "unavailable",
    "conflict",
]


class VariationDifference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: DifferenceCategory
    path: str
    label: str
    before: Any = None
    after: Any = None
    units: str | None = None
    material: bool = True


class ImmutableVariationLayer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    payload: dict[str, Any]
    sha256: str

    @model_validator(mode="after")
    def validate_payload_hash(self) -> ImmutableVariationLayer:
        expected = canonical_payload_sha256(self.payload)
        if self.sha256 != expected:
            raise ValueError(
                "Immutable variation-layer SHA-256 does not match its canonical payload."
            )
        return self


class VariationAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_id: str
    run_id: str
    relationship: AttemptRelationship
    package_identity_sha256: str
    accepted_backing: bool = False


class VariationValidationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal[
        "specification",
        "package",
        "attempt_integrity",
        "output_completeness",
        "world_inspectability",
        "availability",
        "parent_eligibility",
    ]
    disposition: Literal["pending", "passed", "caveated", "failed"]
    reason: str


class VariationEnvelope(BaseModel):
    """Small shared envelope around one explicit World/Recipe payload."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cloud_world_variation_v1"] = VARIATION_ENVELOPE_SCHEMA_VERSION
    world_id: str
    recipe_id: str
    recipe_contract_version: str
    simulation_id: str
    parent_simulation_id: str
    reference_simulation_id: str
    display_name: str
    question: str | None = None
    scientific_design: ImmutableVariationLayer
    numerical_realization: ImmutableVariationLayer
    observation_plan: ImmutableVariationLayer
    world_payload: dict[str, Any]
    differences: list[VariationDifference]
    relationship_classification: RelationshipClassification
    run_profile_id: str
    run_profile_contract: dict[str, Any]
    cost_estimate: dict[str, Any]
    launch_review_snapshot_id: str | None = None
    package_identity_sha256: str | None = None
    attempts: list[VariationAttempt] = Field(default_factory=list)
    validation_decisions: list[VariationValidationDecision] = Field(default_factory=list)
    availability_state: AvailabilityState = "intended"
    parent_eligible: bool = False
    parent_eligibility_reason: str = "Parent eligibility is evaluated after output validation."

    @model_validator(mode="after")
    def validate_immutable_identity(self) -> VariationEnvelope:
        scientific_controls = self.scientific_design.payload.get("controls")
        world_controls = self.world_payload.get("controls")
        if scientific_controls != world_controls:
            raise ValueError(
                "World controls do not match the immutable scientific-design controls."
            )
        material_categories = {
            difference.category for difference in self.differences if difference.material
        }
        if self.relationship_classification == "observation_only_attempt":
            if material_categories != {"observation_plan"}:
                raise ValueError("Observation-only attempts may change only the observation plan.")
            if self.simulation_id != self.parent_simulation_id:
                raise ValueError(
                    "Observation-only attempts must remain beneath the same Simulation."
                )
            return self
        identity = canonical_payload_sha256(
            {
                "scientific_design": self.scientific_design.payload,
                "numerical_realization": self.numerical_realization.payload,
            }
        )
        if not self.simulation_id.endswith(f"_{identity[:8]}"):
            raise ValueError(
                "Simulation ID hash suffix does not match the immutable scientific and "
                "numerical identity."
            )
        return self


def canonical_payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def immutable_layer(payload: dict[str, Any]) -> ImmutableVariationLayer:
    return ImmutableVariationLayer(payload=payload, sha256=canonical_payload_sha256(payload))


def classify_relationship(
    differences: list[VariationDifference],
) -> RelationshipClassification:
    material = [difference for difference in differences if difference.material]
    physical = [
        difference
        for difference in material
        if difference.category
        in {
            "terrain",
            "wind",
            "moisture",
            "stability_thermodynamics",
            "forcing_initiation",
        }
    ]
    numerical = [
        difference for difference in material if difference.category == "numerical_realization"
    ]
    observation = [
        difference for difference in material if difference.category == "observation_plan"
    ]
    if physical and (numerical or observation):
        return "mixed_variation"
    if numerical:
        return "numerical_sensitivity"
    if physical:
        if all(_is_deterministic_initiation_difference(difference) for difference in physical):
            return "controlled_initiation_sensitivity"
        return (
            "controlled_physical_variation"
            if len(physical) == 1
            else "multi_factor_physical_variation"
        )
    if observation:
        return "observation_only_attempt"
    raise ValueError("A variation requires a physical or numerical difference.")


def _is_deterministic_initiation_difference(difference: VariationDifference) -> bool:
    return difference.category == "forcing_initiation" and difference.path.startswith(
        "controls.thermal_"
    )


def grouped_differences(
    differences: list[VariationDifference],
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "terrain": [],
        "wind": [],
        "moisture": [],
        "stability/thermodynamics": [],
        "forcing/initiation": [],
        "numerical realization": [],
        "observation plan": [],
    }
    group_names = {
        "terrain": "terrain",
        "wind": "wind",
        "moisture": "moisture",
        "stability_thermodynamics": "stability/thermodynamics",
        "forcing_initiation": "forcing/initiation",
        "numerical_realization": "numerical realization",
        "observation_plan": "observation plan",
    }
    for difference in differences:
        groups[group_names[difference.category]].append(
            {
                "path": difference.path,
                "label": difference.label,
                "before": difference.before,
                "after": difference.after,
                "units": difference.units,
                "material": difference.material,
            }
        )
    return groups
