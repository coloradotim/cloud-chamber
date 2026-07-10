# Sounding Candidate Screening Contract

Status: v1 product/data contract

Cloud Chamber sounding candidates are pre-run hypotheses for choosing an
observed atmosphere to try in CM1. They are not forecasts, verification, or
proof that a run will form cloud, rain, or suppression. CM1 output remains the
source of truth.

The browser does not parse IGRA station text, ZIP archives, or raw NetCDF.
Candidate screening and analysis are backend-owned and use cached IGRA station
text plus runtime-local cache metadata.

## Current Story Set

The v1 candidate stories are:

- `shallow_cumulus_candidate`
- `dry_failed_candidate`
- `capped_suppressed_candidate`
- `humid_rainy_candidate`
- `severe_thunderstorm_environment`
- `supercell_environment`
- `high_cape_pulse_storm`
- `dry_microburst_inverted_v`
- `squall_line_cold_pool_candidate`
- `elevated_convection`
- `needs_review`
- `poor_or_incomplete_candidate`

Visible labels may be friendlier, but every visible story must be backed by
`story_scores`, feature values, evidence items, caveats, and package readiness.
Deep-convection-oriented stories are pre-run hypotheses for Deep Convection
Trial routing, not outcome claims.

## Feature Inputs

The backend derives several feature groups from the selected IGRA sounding
after converting source height to model height above the station. Not every
derived or displayed field directly changes the story score.

### Scoring Inputs

The current story scores primarily use:

- data completeness score
- mean qv from 0-1000 m
- estimated LCL
- lapse rate from 0-1 km
- inversion/cap strength proxy
- moisture depth above a 6 g/kg qv threshold
- low-level to midlevel qv drop / dry-layer proxy

Missing scoring inputs weaken/caveat story support instead of being interpreted
as meaningful physical zero values.

### Evidence / Context Fields

The candidate UI may also display these fields as evidence or context:

- lowest usable model level
- profile top
- low-level qv
- mean qv from 0-500 m
- surface or lowest-level temperature-dewpoint spread
- lapse rate from 0-3 km
- cap height proxy
- observed wind availability
- midlevel lapse rate when available
- bulk shear from 0-1, 0-3, and 0-6 km when observed winds exist
- dry microburst / inverted-V proxy
- freezing-level proxy
- package readiness

These fields help explain the sounding and package path. They do not directly
drive story scores unless the implementation and tests are updated to say so.

### Package-Readiness Fields

Package readiness is determined by the observed-sounding parser and
normalization path. It depends on station metadata and usable CM1-facing
profile fields, including:

- station elevation and model-z conversion
- enough usable levels
- profile top high enough for the selected domain
- lowest usable level close enough to the model bottom
- monotonic and finite converted levels
- required thermodynamic fields
- observed u/v wind components

The v1 screen does not compute CAPE, CIN, LFC, EL, storm-relative helicity,
map/GIS forcing, or radar/precipitation predictors. Those require separate
research, diagnostics, and validation before becoming product-facing evidence.

## Story Logic

Scores are 0-100 candidate-selection aids. They are weighted heuristics, not
probabilities. A score of `supported` means the available sounding-derived
features support trying that story; it does not mean CM1 will produce that
outcome.

### Cloud-Forming Shallow Cumulus Candidate

Scoring primarily uses:

- moderate to high mean qv from 0-1 km
- low to moderate estimated LCL
- deeper moisture depth
- weak to moderate cap proxy
- useful low-level lapse rate
- profile completeness

Evidence also shows low-level qv, 0-500 m qv, 0-1 km qv, T-Td spread,
estimated LCL, low-level and 0-3 km lapse rates, moisture depth, cap
strength/height context, profile coverage, wind availability, and package
readiness.

Package readiness depends on the observed-sounding parser and normalization
path, including usable model-z conversion, profile depth, required
thermodynamic fields, and observed u/v winds.

High support requires moisture, plausible LCL, thermal support, weak or
moderate cap, and good data completeness. Missing moisture, LCL, lapse-rate,
cap, or moisture-depth inputs caveat the score and push the candidate toward
`needs_review`.

### Dry Failed Cumulus Candidate

Scoring primarily uses:

- low mean qv from 0-1 km
- high estimated LCL
- shallow moisture depth
- midlevel dry-layer proxy
- useful low-level lapse rate
- profile completeness

Evidence also shows low-level qv, 0-500 m qv, 0-1 km qv, T-Td spread,
estimated LCL, low-level and 0-3 km lapse rates, moisture depth, dry-layer
proxy, profile coverage, wind availability, and package readiness.

Package readiness depends on the observed-sounding parser and normalization
path, including usable model-z conversion, profile depth, required
thermodynamic fields, and observed u/v winds.

Missing moisture is not treated as dry air. Missing qv, LCL, moisture-depth,
or dry-layer inputs produce caveats and weak or unavailable support rather than
a confident dry-failed label.

### Capped / Suppressed Candidate

Scoring primarily uses:

- mean qv from 0-1 km
- plausible estimated LCL
- strong inversion/cap proxy
- useful low-level lapse rate
- profile completeness

Evidence also shows low-level qv, 0-500 m qv, 0-1 km qv, T-Td spread,
estimated LCL, low-level and 0-3 km lapse rates, cap strength, cap height,
moisture depth, profile coverage, wind availability, and package readiness.

Package readiness depends on the observed-sounding parser and normalization
path, including usable model-z conversion, profile depth, required
thermodynamic fields, and observed u/v winds.

This story supports the hypothesis that moisture and thermals may exist but a
stable layer could limit depth. It does not prove that CM1 will suppress cloud
growth.

### Humid / Rainy Candidate

Scoring primarily uses:

- high mean qv from 0-1 km
- low estimated LCL
- deep moisture
- weak cap proxy
- profile completeness

Evidence also shows low-level qv, 0-500 m qv, 0-1 km qv, T-Td spread, LCL,
low-level and 0-3 km lapse rates, moisture depth, weak-cap support, profile
coverage, wind availability, and package readiness.

Package readiness depends on the observed-sounding parser and normalization
path, including usable model-z conversion, profile depth, required
thermodynamic fields, and observed u/v winds.

This story is deliberately caveated because current packages still use
idealized local forcing. It should be read as “humid atmosphere worth trying,”
not as a rain forecast.

### Needs Review

Scoring primarily uses:

- weak data completeness
- missing story-driving features
- screening uncertainty
- package-ready profiles whose evidence is not strong enough for a clear story

Evidence also shows whatever profile, moisture, stability, wind, and
package-readiness context is available.

`needs_review` can still be package-ready. It means the sounding may be worth
manual inspection, not that it is unusable.

### Poor Or Incomplete Candidate

Scoring primarily uses:

- blocked package generation

Package readiness depends on:

- missing station elevation or unsafe height conversion
- too few usable levels
- profile top too low for the selected domain
- lowest usable level too far above model bottom
- nonmonotonic or nonfinite converted levels
- missing required observed winds

Evidence also shows any available profile, moisture, stability, wind, and
package-readiness context so the UI can explain why the candidate is blocked.

Poor/incomplete candidates are not package-ready in the current path. They may
still be useful after parser, station metadata, or profile-quality improvements,
but the UI must show why they are blocked.

## Missing Data Rules

Missing physical evidence is not interpreted as a physical condition. For
example:

- missing qv is not dry air;
- missing LCL is not a high LCL;
- missing cap proxy is not a weak cap;
- missing wind is a package-readiness blocker for the current external-sounding
  path.

Missing features become score caveats and evidence caveats. Blocked parser or
normalization states become `poor_or_incomplete_candidate`.

## Package Readiness

A package-ready candidate has a selected observed sounding payload that can
enter the current external-sounding package path. Package readiness depends on
the parser and normalization contract, including station elevation, model-z
conversion, profile depth, required thermodynamic fields, and observed u/v wind
components.

Candidate screening metadata may be copied into `run_manifest.json`,
`case_manifest.json`, and `dry_run_report.json` as provenance when a candidate
is used to create a package. If the candidate was saved with tags or notes,
those annotations may also be copied into package user metadata and run-status
payloads so the generated package remains tied to the reason it was selected.

## UI Contract

Candidate cards and details must keep this language:

- Screening guidance only.
- Candidate scores are pre-run hypotheses.
- CM1 decides what actually happens.

The backend analysis API owns default recommendations, interest reasons,
discovery buckets, story/story-family/support/readiness/station-search
refinements, and sort-key ordering. The default UI should answer which cached
soundings are interesting and why before exposing advanced refinements. It must
display the backend-returned candidate list rather than parsing raw sounding
files or recomputing story scores in the browser. Analysis must include
secondary story matches when `story_scores` contain meaningful support for the
selected story. Missing feature values must remain unavailable/caveated and sort
last instead of becoming zero-valued evidence. The UI must not show a confident
story label without evidence, caveats, and package readiness.

Saved candidates may carry freeform tags and notes such as `Deep convection
candidates`, `Surface-forced candidates`, `Needs longer run`, `Needs finer
output cadence`, `Maybe rerun`, and `Needs review`. These annotations are
runtime-local pre-run organization metadata; they are not Results and are not
committed.

## Testing Contract

Automated tests use tiny synthetic IGRA-style fixtures or direct deterministic
feature dictionaries. Tests must not fetch live NOAA/NCEI data, run CM1, parse
station text in the browser, or commit cached station files.

Tests should prove:

- every current story can be produced deterministically;
- every story has reasons and evidence;
- missing features caveat or weaken support instead of producing confident
  labels;
- backend analysis works across multiple cached sounding blocks;
- physical-field sorting keeps missing values last;
- default recommendations and interest reasons are backend-owned;
- story, support, and readiness refinements are backend-owned;
- saved tags and notes round-trip through runtime-local JSON;
- saved tags and notes follow a used candidate into package metadata;
- poor/incomplete candidates are blocked from package generation;
- package-ready but weak profiles become `needs_review`;
- candidate-screening provenance is copied into generated package metadata
  when provided.
