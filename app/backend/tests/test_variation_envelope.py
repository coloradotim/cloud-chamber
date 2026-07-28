import pytest

from cloud_chamber.variation_envelope import (
    DifferenceCategory,
    VariationDifference,
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
def test_relationship_classification_is_shared_and_category_driven(
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
