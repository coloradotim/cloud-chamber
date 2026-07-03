# Sounding Candidate Screening Contract

Status: v1 product/data contract

Cloud Chamber sounding candidates are pre-run hypotheses for choosing an
observed atmosphere to try in CM1. They are not forecasts, verification, or
proof that a run will form cloud, rain, or suppression. CM1 output remains the
source of truth.

The browser does not parse IGRA station text, ZIP archives, or raw NetCDF.
Candidate screening is backend-owned and uses cached IGRA station text plus
runtime-local cache metadata.

## Current Story Set

The v1 candidate stories are:

- `shallow_cumulus_candidate`
- `dry_failed_candidate`
- `capped_suppressed_candidate`
- `humid_rainy_candidate`
- `needs_review`
- `poor_or_incomplete_candidate`

Visible labels may be friendlier, but every visible story must be backed by
`story_scores`, feature values, evidence items, caveats, and package readiness.

## Feature Inputs

The current backend scoring logic derives these features from the selected
IGRA sounding after converting source height to model height above the station:

- data completeness score
- lowest usable model level
- profile top
- low-level qv
- mean qv from 0-500 m
- mean qv from 0-1000 m
- surface or lowest-level temperature-dewpoint spread
- estimated LCL
- lapse rate from 0-1 km
- lapse rate from 0-3 km
- inversion/cap strength proxy
- cap height proxy
- moisture depth above a 6 g/kg qv threshold
- low-level to midlevel qv drop / dry-layer proxy
- observed wind availability
- package readiness

The v1 screen does not compute CAPE, CIN, LFC, EL, storm-relative helicity,
map/GIS forcing, or radar/precipitation predictors. Those require separate
research, diagnostics, and validation before becoming product-facing evidence.

## Story Logic

Scores are 0-100 candidate-selection aids. They are weighted heuristics, not
probabilities. A score of `supported` means the available sounding-derived
features support trying that story; it does not mean CM1 will produce that
outcome.

### Cloud-Forming Shallow Cumulus Candidate

Uses:

- moderate to high mean qv from 0-1 km
- low to moderate estimated LCL
- deeper low-level moisture
- weak to moderate cap proxy
- useful low-level lapse rate
- profile completeness

Evidence shown includes low-level qv, 0-500 m qv, 0-1 km qv, T-Td spread,
estimated LCL, low-level lapse rate, moisture depth, cap proxy, profile
coverage, and package readiness.

High support requires moisture, plausible LCL, thermal support, weak or
moderate cap, and good data completeness. Missing moisture, LCL, lapse-rate,
cap, or moisture-depth inputs caveat the score and push the candidate toward
`needs_review`.

### Dry Failed Cumulus Candidate

Uses:

- low mean qv from 0-1 km
- high estimated LCL or large T-Td spread
- shallow moisture depth
- midlevel dry-layer proxy
- useful low-level lapse rate
- profile completeness

Evidence shown includes qv, T-Td spread, estimated LCL, low-level lapse rate,
moisture depth, dry-layer proxy, and package readiness.

Missing moisture is not treated as dry air. Missing qv, LCL, moisture-depth,
or dry-layer inputs produce caveats and weak or unavailable support rather than
a confident dry-failed label.

### Capped / Suppressed Candidate

Uses:

- available low-level moisture
- plausible estimated LCL
- strong inversion/cap proxy
- cap height proxy
- useful low-level lapse rate
- profile completeness

Evidence shown includes low-level moisture, estimated LCL, lapse rate, cap
strength, cap height, profile coverage, and package readiness.

This story supports the hypothesis that moisture and thermals may exist but a
stable layer could limit depth. It does not prove that CM1 will suppress cloud
growth.

### Humid / Rainy Candidate

Uses:

- high low-level qv
- low estimated LCL
- deep moisture
- weak cap proxy
- profile completeness

Evidence shown includes qv, LCL, moisture depth, weak-cap support, profile
coverage, and package readiness.

This story is deliberately caveated because current packages still use
idealized local forcing. It should be read as “humid atmosphere worth trying,”
not as a rain forecast.

### Needs Review

Uses:

- weak data completeness
- missing story-driving features
- screening uncertainty
- package-ready profiles whose evidence is not strong enough for a clear story

`needs_review` can still be package-ready. It means the sounding may be worth
manual inspection, not that it is unusable.

### Poor Or Incomplete Candidate

Uses:

- blocked package generation
- missing station elevation or unsafe height conversion
- too few usable levels
- profile top too low for the selected domain
- lowest usable level too far above model bottom
- nonmonotonic or nonfinite converted levels
- missing required observed winds

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
is used to create a package.

## UI Contract

Candidate cards and details must keep this language:

- Screening guidance only.
- Candidate scores are pre-run hypotheses.
- CM1 decides what actually happens.

The UI may filter by a target story, but it must include secondary story
matches when `story_scores` contain meaningful support for the selected story.
It must not show a confident story label without evidence, caveats, and package
readiness.

## Testing Contract

Automated tests use tiny synthetic IGRA-style fixtures or direct deterministic
feature dictionaries. Tests must not fetch live NOAA/NCEI data, run CM1, parse
station text in the browser, or commit cached station files.

Tests should prove:

- every current story can be produced deterministically;
- every story has reasons and evidence;
- missing features caveat or weaken support instead of producing confident
  labels;
- poor/incomplete candidates are blocked from package generation;
- package-ready but weak profiles become `needs_review`;
- candidate-screening provenance is copied into generated package metadata
  when provided.
