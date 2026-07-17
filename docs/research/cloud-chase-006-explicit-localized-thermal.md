# Cloud Chase 006: Explicit Localized Thermal

Status: positive-control passed; Topeka contrast failed to form cloud

## Question

Can Cloud Chamber preserve the smallest honest localized-thermal setup that
produces one growing cloud in a known-capable atmosphere without escalating to
an arbitrarily strong trigger?

This is not daytime evolution. It is not an observed boundary, forecast, or
claim of spontaneous convection. Product copy should label it:

```text
Explicit localized thermal
```

## CM1 Source Inspection

Configured CM1 source: `cm1r21.1/src/init3d.F`

Source hash measured before the runs:
`9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28`

Executable identity: `cm1r21.1/run/cm1.exe`

Executable hash measured before the runs:
`5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1`

Stock CM1 r21.1 `iinit = 1` implements one warm bubble:

- Bubble count: 1.
- Center: domain center horizontally.
- Center height: 1400 m AGL in source.
- Horizontal radius: 10000 m.
- Vertical radius: 1400 m.
- Maximum potential-temperature perturbation: 1.0 K.
- Shape: cosine-squared ellipsoid for `beta < 1`.
- qv behavior: no direct qv perturbation; source sets `maintain_rh = .false.`.
- Pressure balancing: Cloud Chamber namelist used `ibalance = 0`, so no
  pressure-balancing solve was applied.

The first output frame confirmed the imposed thermal was comparable in both
runs: maximum theta anomaly about 0.96 K at the domain center near the 1.25 km
scalar level, with zero qv anomaly.

## Recipe Setup

Recipe: `explicit_localized_thermal_v0`

Run shape for both cases:

- Domain: 120 km x 120 km.
- Grid: 120 x 120 x 40.
- Model top: 20 km.
- Duration: 60 simulated minutes.
- Output cadence: 5 minutes.
- Time step: 6 s.
- Surface heat and moisture fluxes: disabled.
- Radiation, terrain/GIS surface initialization, and large-scale forcing:
  disabled/not part of v0.
- Output fields: current full output set.

The recipe exposes no raw trigger controls in the UI. It is a fixed benchmark
probe using stock CM1 `iinit = 1`.

## Fort Worth Positive Control

Case: Fort Worth `USM00072249`, valid `1997-05-27T00:00:00Z`.

Normalized sounding: exact `input_sounding` from the prior successful Fort
Worth Deep-Tower run, hash
`08a9012ff831568cf6af45713d217a6c448067a85a459e830f40aed00d6826a5`.

Run ID: `cloud_chase_006-fort_worth_explicit_localized_thermal_60min`.

Runtime integrity: completed normally and auto-ingested; runtime caveat was
underflow-only.

Outcome:

- First liquid cloud: 20 minutes.
- Liquid cloud top: grew from 1.25 km to 1.75 km.
- Maximum cloud water: `8.82e-4 kg/kg` at 40 minutes.
- Maximum updraft: `1.31 m/s` at 60 minutes.
- Rain water aloft: trace, maximum `2.77e-7 kg/kg`.
- Surface rain: trace, maximum `6.42e-12 cm`.
- Post-initial reflectivity: weak trace, peak about `-27.6 dBZ`.
- Visual-interest rating: 2/5.

Fort Worth passed the positive-control gate because the modest stock thermal
produced a real growing shallow cloud with sustained cloud water and weak
precipitation traces.

## Topeka Contrast

Case: Topeka/Mun., Kansas `USM00072456`, valid `2017-06-18T00:00:00Z`.

Normalized sounding: exact `input_sounding` from Cloud Chase 005, hash
`38304066848f39f66e265872456d5f3f39bf7f2db3078b42b0bbd51b1564b392`.

Run ID: `cloud_chase_006-topeka_explicit_localized_thermal_60min`.

Runtime integrity: completed normally and auto-ingested; runtime caveat was
underflow-only.

Outcome:

- First liquid cloud: none.
- Liquid cloud top: none.
- Maximum cloud water: `0 kg/kg`.
- Maximum updraft: `0.65 m/s` at 5 minutes, then decayed below `0.30 m/s`.
- Rain water aloft: none.
- Surface rain: none.
- Post-initial reflectivity: no hydrometeor signal; `-35.2 dBZ` field floor.
- Visual-interest rating: 1/5.

Topeka received the same initial localized thermal but did not form cloud.

## Interpretation

The stock `iinit = 1` setup is modest enough to pass an honesty check: it does
not force every supported-looking sounding to make a cloud. Fort Worth and
Topeka responded differently even though the imposed thermal was materially the
same. That makes the recipe useful as a bounded exploratory probe, not as a
guaranteed cloud-maker.

The Fort Worth response was shallow, not a deep tower. The positive control
therefore validates only this narrow claim: a fixed 1 K localized thermal can
produce a growing cloud in a known-capable atmosphere under Cloud Chamber's
coarse storm-scale setup.

## Decision

C. It works for Fort Worth but not Topeka; preserve it as a benchmark while
treating atmospheric response as case-dependent.

Recommendation: preserve `explicit_localized_thermal_v0` as an exploratory
benchmark probe with explicit trigger assumptions and no product-facing trigger
editor.
