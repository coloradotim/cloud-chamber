# Sounding Candidate Screening Contract

**Status:** Implemented contract

## Purpose

This contract documents the current implemented screening behavior for cached
IGRA sounding candidates, including deterministic story scores, evidence
records, caveats, package-readiness state, saved candidate annotations,
candidate-to-package provenance, and current backend/frontend interfaces.

## Authority Boundary

This is a current implementation contract. It does not define final product
architecture, final recommendation policy, supported Cloud Worlds, supported
Recipes, or future analyzer behavior.

Current implementation labels such as `story`, `story_scores`, `candidate`,
`run_recipe`, Build, Results, and Explore are subordinate to
`docs/product/APPLICATION_SEMANTICS.md`. Current code and tests remain the
source of truth for implemented behavior.

## Current Implemented Model

The current screening version is `sounding-screening-v3`. The current sounding
diagnostics version is `sounding-diagnostics-v1`.

Screening reads cached IGRA station text files from the runtime cache manifest,
summarizes available soundings, parses selected observed soundings, computes
bounded diagnostic features, and returns `SoundingCandidate` records. Each
candidate includes station metadata, valid time, source file name, source file
hash, source provider/format, selected sounding payload when parsing succeeds,
features, evidence, caveats, story scores, package readiness, and created time.

Current story identifiers are implementation classifier labels:

- `shallow_cumulus_candidate`;
- `dry_failed_candidate`;
- `capped_suppressed_candidate`;
- `humid_rainy_candidate`;
- `severe_thunderstorm_environment`;
- `supercell_environment`;
- `high_cape_pulse_storm`;
- `dry_microburst_inverted_v`;
- `squall_line_cold_pool_candidate`;
- `elevated_convection`;
- `needs_review`;
- `poor_or_incomplete_candidate`.

Current story families are `lower_atmosphere`, `deep_convection`, and `review`.

Implemented deterministic feature inputs include data completeness, profile
depth, lowest usable level, usable lower-level counts, temperature, pressure,
moisture, derived dewpoint, estimated LCL, low-level and layer-mean qv,
moisture depth, qv drop, precipitable-water proxy, lapse-rate proxies,
inversion/cap proxies, simple surface-based and mixed-layer parcel diagnostics,
LFC/EL estimates, observed wind availability, wind-profile depth, bulk shear,
SRH placeholders, dry-microburst/inverted-V proxy, freezing level, and
near-surface discontinuity evidence.

`StoryScore.support` is assigned deterministically from the story score:
`supported` at 65 or higher, `weak` from 35 through less than 65, and
`unavailable` below 35. Candidate `confidence` is `low`, `medium`, or `high`
from package readiness, rank score, and completeness.

`deep_tower_opportunity` is an experimental numeric heuristic stored in
candidate features and evidence. It remains an evidence/sort field only. A high
value is not a reliable fixed-recipe recommendation and must not automatically
authorize expensive compute. Current high values are intentionally summarized as
experimental evidence rather than as supported Deep-Tower scout advice.

The current near-surface guardrail prevents a major near-surface discontinuity
from producing clean Deep-Tower support: surface-based CAPE is ignored for that
experimental heuristic, mixed-layer CAPE becomes the primary buoyancy input, and
the experimental score is capped below the old supported tier.

## Behavioral Rules And Invariants

Candidate scores are deterministic screening heuristics. They are not
probabilities, forecasts, Simulation outcomes, scientific validation, or proof
that CM1 will produce cloud, rain, suppression, rotation, cold-pool behavior, or
visual interest.

Missing physical evidence is not interpreted as a physical zero. Missing or
unsupported evidence appears as unavailable features, caveats, weaker support,
or blocked package-readiness state.

`package_ready` means the parsed sounding currently has a selected normalized
payload that can attempt the current package-generation path. It does not make
the candidate an approved Recipe and does not guarantee that pre-run validation
or CM1 execution will succeed.

Deep-convection `story` labels remain broad ingredient classifiers. They are
not a canonical Deep-Tower recommendation. The fixed Deep-Tower Benchmark may be
available for deliberate comparison when the user configures it, but screening
does not make that compute automatically worthwhile.

No candidate, score, story, saved candidate, readiness state, or `run_recipe`
label creates a Cloud World, Recipe, Simulation, Exploration, or Experiment.

## Current Ownership And Interfaces

The backend owns cached-station discovery, IGRA parsing, diagnostic feature
calculation, story scoring, support states, caveats, package-readiness state,
saved candidate persistence, sorting, filtering, and candidate analysis payloads.

The frontend owns current candidate presentation, filter controls, saved
candidate interactions, and copying selected candidate metadata into run-plan
and package requests. It does not own the scoring rules and does not validate
the science of a candidate by rendering it.

Current API routes include:

- `/api/sounding-candidates/screening-inputs`;
- `/api/sounding-candidates/screen`;
- `/api/sounding-candidates/analyze`;
- `/api/sounding-candidates/saved`;
- `/api/sounding-candidates/saved/{saved_candidate_id}`.

`/api/sounding-candidates/analyze` is backend-owned for filtering and sorting.
Its default `sort_by` is `best_match`. In a deep-convection scope, `best_match`
uses the strongest relevant scoped deep-story score. The explicit
`deep_tower_opportunity` sort uses the experimental numeric field. These
orderings can differ.

In deep-convection scope, visible support and support filtering currently use
`deep_tower_opportunity_support`. The field remains experimental evidence, not a
canonical Recipe recommendation.

Saved candidates are stored in:

```text
<runtime-cache>/sounding-candidates/saved_candidates.json
```

Saved records preserve the candidate, selected sounding payload, screening
version, primary story, story family, story scores, features, evidence, caveats,
tags, notes, timestamps, and linked run/result identifiers when present.

When a selected candidate is used to generate a package, frontend metadata is
copied into the `candidate_screening` payload. Package generation preserves that
payload in `run_manifest.json`, `case_manifest.json`, and `dry_run_report.json`.
Pre-run validation also records selected candidate, selected implementation
story, selected `run_recipe`, required output fields, alignment status, caveats,
and blocking errors.

## Persistence Or Runtime Records

Candidate screening reads from the current runtime cache manifest and cached
IGRA station text files. It does not currently create a durable product object
for every analyzed sounding.

Saved candidate annotations are runtime-local JSON records under the configured
cache directory. Generated packages copy selected candidate provenance into the
run directory, but that copy remains current run/package metadata rather than a
final product evidence model.

## Terminology Mapping

- **story**: current implementation classifier label for a pre-run screening
  interpretation; not a product story system.
- **story_scores**: deterministic current screening outputs; not forecasts or
  probabilities.
- **candidate**: current cached sounding plus diagnostics and screening
  metadata; not a Cloud World, Recipe, Simulation, Exploration, or Experiment.
- **screening score**: heuristic ingredient ranking value, not scientific
  validation.
- **package readiness**: compatibility with current package-generation
  machinery, not Recipe approval.
- **run_recipe**: current code-level run-generation label; not canonical Recipe
  semantics.
- **Recipe**: approved product-semantic term for a complete, known-working,
  modifiable simulation design within a Cloud World.
- **Experiment**: approved product-semantic term for deliberate exploration
  structured around a question or controlled comparison; not a package, run,
  result, or saved candidate.
- **Simulation**: approved product-semantic term for one evolving modeled cloud
  or cloud field the user watches.

## Evidence Map

Implementation evidence:

- `app/backend/cloud_chamber/sounding_candidates.py`;
- `app/backend/cloud_chamber/sounding_diagnostics.py`;
- `app/backend/cloud_chamber/observed_sounding.py`;
- `app/backend/cloud_chamber/igra_catalog.py`;
- `app/backend/cloud_chamber/igra_recent_cli.py`;
- `app/backend/cloud_chamber/pre_run_validation.py`;
- `app/backend/cloud_chamber/dry_run_package.py`;
- `app/backend/cloud_chamber/cm1_input_contract.py`;
- `app/backend/cloud_chamber/run_manifest.py`;
- `app/backend/cloud_chamber/app.py`;
- `app/frontend/src/App.tsx`.

Tests:

- `app/backend/tests/test_sounding_candidates.py`;
- `app/backend/tests/test_sounding_diagnostics.py`;
- `app/backend/tests/test_observed_sounding.py`;
- `app/backend/tests/test_igra_catalog.py`;
- `app/backend/tests/test_igra_recent_cli.py`;
- `app/backend/tests/test_dry_run_package.py`;
- `app/backend/tests/test_app.py`;
- `app/frontend/src/App.test.tsx`;
- `app/frontend/e2e/mocked-smoke/build-results-explore.spec.ts`.

## Known Implementation Limits

The current analyzer uses deterministic heuristics and simple diagnostics,
including simple parcel estimates. It is not an independent trusted parcel
analysis package and does not predict the actual CM1 response.

The current product analyzer reads the implemented cache collection available
through the runtime cache workflow. It does not by itself define candidate
supply strategy or period-of-record search policy.

Current saved candidate persistence is runtime-local JSON. There is no final
database, collaborative review, or durable product evidence model in this
contract.

Current pre-run validation still contains some legacy implementation vocabulary,
including `selected_hypothesis` and a small `predicted_output_signature` list.
Those fields are current package/validation payload fields only and do not
activate the archived analyzer-hypothesis or output-signature proposal.

## Non-Implications

This contract does not approve a future analyzer hypothesis object, predicted
output-signature system, story-to-Recipe product mapping, recommendation
platform, station blacklist, candidate-supply strategy, or automatic
compute-spending policy.

It does not choose observed soundings as the primary future product path, does
not approve any current `run_recipe` as a canonical Recipe, and does not make a
candidate-screening result an Experiment.
