# Thermal Fate Process Diagnostics

This document is the initial product contract for Cloud Chamber's Thermal Fate
Framework. Issue #148 owns the deeper diagnostic specification, but current docs
should already point future work toward this center of gravity.

## Product Frame

Cloud Chamber is a CM1-backed workbench for exploring the fate of thermals:

```text
why air rises
why some thermals do or do not form cloud
why some clouds stay shallow
why others grow taller
why some break through into deep convection
how precipitation feedback can reorganize or suppress convection
```

CM1 remains the source of truth. Cloud Chamber may derive diagnostics, labels,
overlays, and explanations from CM1 output, but it must not invent cloud
physics or make unsupported claims.

The central inspection question is:

```text
What happened here?
```

That question should eventually work at three scales:

- **Global run diagnostics**: what happened across the completed CM1 result?
- **Local selected-region diagnostics**: what happened in this point, column, or box?
- **Comparison diagnostics**: what changed between baseline and a variant?

## Thermal Fate Ladder

Use conservative labels that can be marked as supported, candidate, or
insufficient evidence:

```text
No meaningful thermal
Thermal without cloud
Brief / diluted cloud
Fair-weather cumulus
Capped / suppressed cumulus
Growing cumulus
Towering cumulus candidate
Deep-convection candidate
Precipitation-feedback candidate
Insufficient evidence
```

The label is never just a UI mood. It must be backed by CM1 fields or derived
diagnostics, with caveats when fields are missing.

## Scenario Families

Thermal Fate scenario families should be represented as curated CM1 experiments,
not real-time sliders:

- **Moisture-limited thermal fate**: Dry Failed Cumulus and the humidity ladder.
- **Surface-heating-driven thermal fate**: weaker/baseline/stronger heating,
  focused warm patches, patchy heating, and gradients.
- **Cap-limited thermal fate**: Capped / Suppressed Cumulus and later cap-height
  variants.
- **Dry-air-aloft / dilution-limited thermal fate**: cloud edge/top weakening,
  evaporation, and saturation-deficit stories when diagnostics support them.
- **Deep-convection breakthrough**: growing cumulus, towering cumulus, and
  cumulonimbus candidates when CAPE/CIN/LFC/EL and cloud-top/updraft evidence
  exist.
- **Precipitation feedback / cold-pool interaction**: rain onset, downdrafts,
  evaporative cooling, cold pools, outflow, and new lifting where supported.
- **Low stratus / low-cloud layer** where the product needs a non-thermal
  low-cloud contrast.

Baseline Shallow Cumulus remains the first executable Golden Path. It is not
the whole product vision.

## Diagnostic Layers

### Direct CM1 Fields

Initial direct fields include `qc`, `w`, and optional `qr`. Future thermal-fate
work may use `qv`, `th`, pressure/temperature coordinates, and other CM1 fields
when available.

### Derived Diagnostics

Current and near-term derived diagnostics include:

```text
cloud formed yes/no
first cloud time
cloud base/top
cloud fraction time series
qc max time series
w max/min time series
rain onset / qr summary
cloud-top time series
max qc height time series
max w height time series
cap-relative cloud top
```

Future diagnostics should include relative humidity or saturation ratio,
saturation deficit, buoyancy or theta-v proxies, LCL/LFC/CAPE/CIN/EL metadata,
and precipitation-feedback summaries where the source fields support them.

### Proxy Diagnostics

Use proxy language for inferred process evidence:

```text
consistent with dilution / evaporation
suggests cap-limited growth
supports moisture-limited no-cloud outcome
candidate precipitation-feedback signal
```

Do not say a cloud died from entrainment, broke through inhibition, or formed a
cold pool unless the required fields and diagnostics support that claim.

## Selected-Region Inspection

The selected-region Thermal Fate Inspector should eventually let a user choose a
point, column, or box in Explore and ask:

```text
What happened here?
```

The backend should answer with bounded CM1-derived summaries:

```text
local max/min w over time
local max qc over time
first local cloud time
local cloud fraction
local cloud base/top if available
local rain onset if qr exists
local saturation deficit / RH if available
local cap-relative cloud top if available
comparison to whole-domain diagnostics
thermal-fate label, confidence, and caveats
```

The browser should not parse raw NetCDF. Backend APIs own xarray/NetCDF access,
field selection, downsampling, and diagnostic derivation.

## Renderer Sequencing

Renderer decisions follow process needs:

```text
NetCDF ingest
-> global/process diagnostics
-> selected-region diagnostics
-> Thermal Fate overlays in Explore
-> Thermal Fate Inspector UI
-> renderer upgrade decision (#112)
```

Visual polish is valuable, but it should not lead the product direction. If a
renderer upgrade does not help explain thermal fate, defer it.

## Testing Contract

Thermal Fate tests should use tiny synthetic fixtures and temp runtime homes.
CI must not run real CM1 or require local output.

Test coverage should include:

```text
thermal-fate labels
supported / candidate / insufficient-evidence states
global process diagnostics
selected-region diagnostics
comparison diagnostics
deep-breakthrough unavailable/candidate/supported states
precipitation-feedback unavailable/candidate/supported states
surface-heating scenario metadata and package generation
```

Manual QA should focus on qualitative scientific trust: whether the explanation
teaches the right lesson, whether caveats are clear, and whether the visual
interpretation feels physically believable.
