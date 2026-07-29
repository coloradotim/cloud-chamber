import pytest

from cloud_chamber.variation_envelope import (
    DifferenceCategory,
    ImmutableVariationLayer,
    VariationDifference,
    VariationEnvelope,
    canonical_payload_sha256,
    classify_relationship,
    grouped_differences,
    immutable_layer,
)


def difference(category: DifferenceCategory, path: str = "control") -> VariationDifference:
    return VariationDifference(
        category=category,
        path=path,
        label=path.replace("_", " ").title(),
        before=1,
        after=2,
    )


@pytest.mark.parametrize(
    ("differences", "expected"),
    [
        ([difference("terrain")], "controlled_physical_variation"),
        (
            [
                difference(
                    "forcing_initiation",
                    "controls.thermal_perturbation_amplitude_k",
                )
            ],
            "controlled_initiation_sensitivity",
        ),
        (
            [difference("forcing_initiation", "controls.surface_moisture_flux_g_kg_m_s")],
            "controlled_physical_variation",
        ),
        (
            [difference("terrain"), difference("wind")],
            "multi_factor_physical_variation",
        ),
        ([difference("numerical_realization")], "numerical_sensitivity"),
        (
            [difference("terrain"), difference("numerical_realization")],
            "mixed_variation",
        ),
        ([difference("observation_plan")], "observation_only_attempt"),
    ],
)
def test_relationship_classification_is_shared_and_semantically_explicit(
    differences: list[VariationDifference],
    expected: str,
) -> None:
    assert classify_relationship(differences) == expected


def test_shared_envelope_hashes_canonical_payloads_and_groups_exact_differences() -> None:
    first = {"wind": {"offset": 2}, "terrain": {"height": 1_500}}
    reordered = {"terrain": {"height": 1_500}, "wind": {"offset": 2}}
    rows = [
        difference("terrain", "terrain.ridge_height_m"),
        difference("observation_plan", "observation.duration_seconds"),
    ]

    assert canonical_payload_sha256(first) == canonical_payload_sha256(reordered)
    assert immutable_layer(first).sha256 == canonical_payload_sha256(first)
    grouped = grouped_differences(rows)
    assert grouped["terrain"][0]["path"] == "terrain.ridge_height_m"
    assert grouped["observation plan"][0]["path"] == "observation.duration_seconds"


def test_relationship_rejects_an_unchanged_specification() -> None:
    with pytest.raises(ValueError, match="requires a physical or numerical difference"):
        classify_relationship([])


def test_immutable_layer_rejects_payload_hash_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        ImmutableVariationLayer(payload={"wind": 12}, sha256="0" * 64)


def test_envelope_rejects_control_and_simulation_identity_mismatch() -> None:
    scientific = {
        "controls": {
            "recipe_id": "boulder_moist_wave",
            "boulder_moist": {"low_level_wind_m_s": 20.0},
        }
    }
    numerical = {"grid": "220 × 1 × 125"}
    identity = canonical_payload_sha256(
        {
            "scientific_design": scientific,
            "numerical_realization": numerical,
        }
    )
    payload = {
        "world_id": "mountain_waves",
        "recipe_id": "boulder_moist_wave",
        "recipe_contract_version": "1",
        "simulation_id": f"mountain_waves_test_{identity[:8]}",
        "parent_simulation_id": "parent",
        "reference_simulation_id": "reference",
        "display_name": "Test",
        "scientific_design": immutable_layer(scientific),
        "numerical_realization": immutable_layer(numerical),
        "observation_plan": immutable_layer({"cadence": 200}),
        "world_payload": {"controls": scientific["controls"]},
        "differences": [difference("wind")],
        "relationship_classification": "controlled_physical_variation",
        "run_profile_id": "quick",
        "run_profile_contract": {},
        "cost_estimate": {},
    }

    VariationEnvelope.model_validate(payload)

    mismatched_controls = {
        **payload,
        "world_payload": {"controls": {"recipe_id": "different"}},
    }
    with pytest.raises(ValueError, match="World controls"):
        VariationEnvelope.model_validate(mismatched_controls)

    mismatched_id = {
        **payload,
        "simulation_id": "mountain_waves_test_deadbeef",
    }
    with pytest.raises(ValueError, match="Simulation ID hash suffix"):
        VariationEnvelope.model_validate(mismatched_id)


def test_observation_only_envelope_retains_simulation_identity() -> None:
    scientific = {"controls": {"cape_j_kg": 2_200}}
    numerical = {"grid": "240 x 240 x 60"}
    payload = {
        "world_id": "supercells",
        "recipe_id": "idealized_isolated_supercell",
        "recipe_contract_version": "1",
        "simulation_id": "supercells_quarter_circle_reference",
        "parent_simulation_id": "supercells_quarter_circle_reference",
        "reference_simulation_id": "supercells_quarter_circle_reference",
        "display_name": "Quarter-Circle Supercell",
        "scientific_design": immutable_layer(scientific),
        "numerical_realization": immutable_layer(numerical),
        "observation_plan": immutable_layer({"cadence_seconds": 60}),
        "world_payload": {"controls": scientific["controls"]},
        "differences": [difference("observation_plan")],
        "relationship_classification": "observation_only_attempt",
        "run_profile_id": "alternate_observation",
        "run_profile_contract": {},
        "cost_estimate": {},
    }

    VariationEnvelope.model_validate(payload)

    with pytest.raises(ValueError, match="same Simulation"):
        VariationEnvelope.model_validate(
            {
                **payload,
                "simulation_id": "supercells_new_simulation",
            }
        )
    with pytest.raises(ValueError, match="only the observation plan"):
        VariationEnvelope.model_validate(
            {
                **payload,
                "differences": [
                    difference("observation_plan"),
                    difference("wind"),
                ],
            }
        )
