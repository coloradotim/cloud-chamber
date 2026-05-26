# Thermal Fate Process Diagnostics

This document is the product and diagnostic contract for Cloud Chamber's Thermal
Fate Framework.

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
overlays, and explanations from CM1 output, but it must not invent cloud physics
or make unsupported claims.

The central inspection question is:

```text
What happened here?
```

That question applies at three scales:

- **Global run diagnostics**: what happened across the completed CM1 result?
- **Local selected-region diagnostics**: what happened in this point, column, or
  box?
- **Comparison diagnostics**: what changed between a baseline and a variant?

The product should feel like a process workbench first and a raw field inspector
second. Users should be able to inspect the physics without needing to know CM1
namelist variables, while technical details remain available when needed.

## Product Principles

### CM1 Is The Truth Source

Cloud Chamber does not simulate the cloud lifecycle itself. CM1 generates the
physical result. Cloud Chamber configures cases, launches/runs CM1 locally,
ingests output, derives diagnostics, and visualizes/explains the result.

Reduced or preview models may support setup guidance, explanation, sanity checks,
or quick expectation-setting, but they are not evidence of cloud evolution.

### Scenario Design Is Interactive; CM1 Is Not Real Time

CM1 runs can take minutes, hours, or longer. Cloud Chamber should not be designed
as a real-time slider toy.

The primary loop is:

```text
choose curated scenario
-> adjust a small number of meaningful atmospheric controls
-> generate/launch CM1 run
-> save/ingest result
-> inspect thermal fate after completion
-> compare against baseline or other variants
```

The interactive product value comes before and after CM1 execution: scenario
design, result inspection, selected-region explanation, and comparison across
saved runs.

### Process Needs Lead Rendering Choices

Renderer upgrades should follow diagnostic and explanation needs. A prettier
cloud renderer is valuable only if it helps users understand thermal fate or
communicate it without weakening scientific honesty.

The preferred sequence is:

```text
NetCDF ingest
-> global/process diagnostics
-> selected-region diagnostics
-> Thermal Fate overlays in Explore
-> Thermal Fate Inspector UI
-> renderer upgrade decision
```

## Thermal Fate Ladder

Use conservative labels that can be marked as `supported`, `candidate`,
`insufficient evidence`, or `unsupported because required fields are missing`.

Labels are never just UI mood. They must be backed by CM1 fields or derived
diagnostics.

| Label | Meaning | Minimum supporting evidence | Common caveats |
| --- | --- | --- | --- |
| No meaningful thermal | The selected region/run does not show meaningful upward motion. | `w` stays below the chosen thermal threshold and no meaningful `qc` appears. | Threshold choice must be documented. A weak event may be missed by coarse output cadence. |
| Thermal without cloud | Upward motion exists but no cloud water forms. | Meaningful `w`; `qc` below cloud threshold or absent; preferably RH/saturation deficit supports lack of saturation. | If RH/qv fields are missing, use moisture-limitation language cautiously. |
| Brief / diluted cloud | Cloud water appears briefly or weakly, then fades. | `qc` exceeds threshold for a short time/few cells; cloud fraction or max `qc` collapses afterward. | Direct entrainment is not diagnosed unless source fields support it. |
| Fair-weather cumulus | Cloud forms and remains shallow/modest. | Persistent `qc`; cloud top remains in shallow-cloud layer or below cap; updrafts remain modest/limited. | Requires cap/cloud-top context to distinguish from growing cumulus. |
| Capped / suppressed cumulus | Moisture and vertical motion exist, but stronger stability/cap limits growth. | Meaningful `w`; cloud top lower than baseline or stalls below cap; reduced `qc`/cloud fraction/rain relative to baseline; cap metadata available or clearly inferred. | If cap metadata is missing, mark candidate/insufficient rather than supported. |
| Growing cumulus | Cloud top rises over time and updraft remains active. | Cloud-top time series increases; max `qc` and/or `w` remain active; cloud persists over multiple output times. | Does not by itself prove deep breakthrough. |
| Towering cumulus candidate | Cumulus grows substantially deeper than shallow baseline but deep-convection evidence is incomplete. | Sustained cloud-top rise, stronger/deeper `w`, deeper cloud depth, possibly rain onset. | If LFC/CAPE/CIN/EL are unavailable, keep candidate language. |
| Deep-convection candidate | The run/region shows evidence consistent with breakthrough toward deep convection. | Cloud top rises above shallow-cloud layer/cap context, sustained updraft above LFC if available, CAPE/CIN/LFC/EL metadata supports breakthrough, precipitation may begin. | Do not claim cumulonimbus without required diagnostics. |
| Precipitation-feedback candidate | Rain/downdraft/cold-pool-related feedback may be affecting updrafts or new lifting. | `qr`/rain onset, downdraft/min `w`, near-surface cooling or theta-v perturbation if available, outflow/new-updraft proxy if available. | Cold-pool/outflow claims require near-surface thermodynamic/wind evidence. |
| Insufficient evidence | The requested label cannot be supported from available fields/diagnostics. | Required fields missing or diagnostics inconsistent. | Show what is missing and what would be needed. |

## Scenario Families

Thermal Fate scenario families should be curated CM1 experiments, not arbitrary
parameter sweeps. The first implementation of each family should change as few
physical factors as practical so comparisons are understandable.

### Moisture-Limited Thermal Fate

Primary question:

```text
Why do some thermals rise but fail to make cloud?
```

Examples:

- Baseline Shallow Cumulus.
- Dry Failed Cumulus.
- Low-level humidity ladder: drier / baseline / more humid.

Key diagnostics:

```text
meaningful w with little/no qc
first cloud time or no-cloud outcome
saturation deficit or RH when available
cloud fraction and max qc time series
comparison to baseline
```

Scientific caution: no cloud is meaningful only if the run still has plausible
vertical motion and usable target fields. No cloud plus no motion is not a valid
moisture-limited result.

### Surface-Heating-Driven Thermal Fate

Primary question:

```text
How does the range and intensity of surface heating change thermal fate?
```

Surface heating controls thermal initiation, thermal strength, boundary-layer
growth, and why one cloud can grow more than nearby clouds.

Staged controls:

```text
surface_heating_intensity:
  weaker
  baseline
  stronger

surface_heating_pattern:
  uniform
  focused_warm_patch
  patchy
  gradient
```

Expected contrasts:

```text
weaker heating -> fewer/weaker thermals, delayed or absent cloud
stronger heating -> stronger thermals, earlier cloud, deeper mixed layer, taller cumulus
focused warm patch -> localized stronger updraft/cloud growth
patchy heating -> multiple thermals with different fates in the same run
gradient -> organized difference in thermal activity across the domain
```

Avoid arbitrary painted heating maps until curated patterns and diagnostics are
trustworthy.

### Cap-Limited Thermal Fate

Primary question:

```text
How does a stronger cap suppress or limit cloud growth even when moisture and thermals are available?
```

Examples:

- Baseline Shallow Cumulus.
- Capped / Suppressed Cumulus.
- Later cap-height variants.

Key diagnostics:

```text
cap/inversion metadata from generated sounding
cloud top relative to cap
cloud-top time series
max qc / cloud fraction lower than baseline
rain absent or reduced relative to baseline
meaningful w below cap
```

Scientific caution: if diagnostics cannot separate cap limitation from moisture
limitation, the result should be marked `candidate` or `needs calibration`, not
claimed as supported cap limitation.

### Dry-Air-Aloft / Dilution-Limited Thermal Fate

Primary question:

```text
Why does cloud water weaken or disappear near cloud edges and tops?
```

This family should explain dilution/evaporation stories only where diagnostics
support them.

Candidate diagnostics:

```text
RH or saturation deficit adjacent to cloud boundary
qc weakening near cloud edge/top
cloud fraction shrinking after peak
cloud top stalling or lowering over time
weakening w near cloud top/cap
negative or weakening buoyancy near cloud edge/top, if available
```

Scientific caution: use proxy language such as `consistent with dilution /
evaporation`. Do not claim direct entrainment measurement unless the diagnostic
method explicitly supports it.

### Deep-Convection Breakthrough

Primary question:

```text
Why does one cumulus keep growing while another stalls below the cap?
```

This is a first-class scenario family. It is not vague future work, though its
implementation may be staged and more expensive than shallow-cumulus cases.

Required or desired diagnostics:

```text
CAPE
CIN
LCL
LFC
EL / equilibrium level
cap strength / cap height
moisture depth
cloud-top time series
cloud-top acceleration or sustained rise
updraft depth
max w height over time
sustained w above LFC
qc/cloud depth
precipitation onset
qr / rain water when present
```

Outcome distinctions:

```text
shallow cumulus
growing cumulus
towering cumulus candidate
deep-convection candidate
cumulonimbus / precipitating deep convection, if supported
```

Scientific caution: if LFC/CAPE/CIN/EL metadata is unavailable, deep-breakthrough
labels should usually remain candidate/insufficient evidence.

### Precipitation Feedback / Cold-Pool Interaction

Primary question:

```text
Once rain forms, does it weaken, reorganize, or trigger convection?
```

Precipitation is not just a `rain yes/no` output. It is a feedback transition.

Before precipitation:

```text
surface heating -> thermal -> cloud growth
```

After precipitation begins:

```text
cloud growth -> precipitation loading / evaporation / downdraft -> cold pool / outflow -> new lifting or updraft suppression
```

Required or desired diagnostics:

```text
qr / rain water
rain onset time
surface rain proxy or precipitation rate if available
min w / downdraft strength
downdraft location and timing
rain-loading proxy
subcloud RH / saturation deficit
evaporative-cooling proxy
near-surface theta_v perturbation
cold-pool footprint
outflow boundary proxy
new updraft initiation along outflow
updraft before/after rain onset
cloud-top evolution before/after rain onset
```

Scientific caution: cold-pool and outflow explanations require near-surface
thermodynamic and motion evidence. Without those fields, use candidate or
unavailable language.

### Low Stratus / Low-Cloud Layer

Low stratus remains useful as a contrast case, but it is not primarily a
thermal-fate story. Treat it as a low-cloud regime contrast unless later product
work gives it its own process framework.

## Diagnostic Layers

### Direct CM1 Fields

Initial direct fields include:

```text
qc: cloud water
w: vertical velocity
qr: rain water, when present
```

Future thermal-fate work may need:

```text
qv: water vapor mixing ratio
th or theta-related fields: potential temperature / thermodynamic state
pressure and/or temperature-related fields
near-surface thermodynamic fields for cold-pool diagnostics
additional hydrometeor fields for deeper/mixed-phase cases
```

CM1 variable names and grids can vary by configuration. Implementation should
map available model fields into product-facing concepts and record missing-field
caveats.

### Derived Diagnostics

Near-term derived diagnostics:

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

Future derived diagnostics:

```text
relative humidity or saturation ratio
saturation deficit
buoyancy or theta-v proxy
LCL / LFC / CAPE / CIN / EL metadata
moisture-depth summary
sustained w above LFC
cloud-top acceleration
updraft depth
precipitation-feedback summaries
cold-pool/outflow proxies
```

### Proxy Diagnostics

Proxy diagnostics should be explicitly labeled. Preferred language:

```text
consistent with dilution / evaporation
suggests cap-limited growth
supports moisture-limited no-cloud outcome
candidate deep-breakthrough signal
candidate precipitation-feedback signal
```

Avoid unsupported causal certainty. Do not say a cloud died from entrainment,
broke through inhibition, or formed a cold pool unless the required fields and
diagnostics support that claim.

## Thresholds And Confidence

Existing cloud/rain thresholds should remain documented and testable:

```text
qc_cloud_threshold_kg_kg = 1e-6
minimum_cloud_grid_cells = 10
qr_rain_threshold_kg_kg = 1e-7
```

Thermal and updraft thresholds should be defined by future implementation work
and recorded in result metadata. They should not be hidden constants.

Every thermal-fate label should carry confidence metadata:

```text
supported
candidate
insufficient_evidence
unsupported_missing_fields
```

A supported label requires direct or derived diagnostics that satisfy the label
criteria. A candidate label means the available diagnostics are suggestive but
incomplete. Insufficient evidence means the product cannot honestly label the
fate. Unsupported missing fields means the needed data was not output or not
ingested.

## Global Run Diagnostics

Global diagnostics summarize the whole completed CM1 result. They should support
result cards, comparison views, and initial Explore defaults.

Minimum global diagnostics:

```text
cloud formed / no cloud
first cloud time
cloud base/top when available
cloud-top time series
cloud fraction time series
max qc and qc max time series
max/min w and w time series
rain present / rain onset when qr is available
main limiting factor if supported
thermal-fate label if supported
caveats / missing fields
```

Global diagnostics should never hide important caveats. Floating-point runtime
warnings can be preserved as caveats while still allowing diagnostics to succeed
if target fields are finite and usable.

## Local Selected-Region Diagnostics

The selected-region Thermal Fate Inspector should let the user choose a point,
column, or box in Explore and ask:

```text
What happened here?
```

The backend should answer with bounded CM1-derived summaries. The browser should
not parse raw NetCDF.

Initial selected-region inputs:

```text
result id
region type: point, column, or box
model/grid or visualization coordinates
neighborhood/box size
time context where needed
```

Initial selected-region outputs:

```text
region metadata and bounds
source result/provenance
local max/min w over time
local max qc over time
first local cloud time
local cloud fraction over time
local cloud base/top if available
local max qc height over time
local max w height over time
local rain onset / max qr if qr exists
local RH / saturation deficit if available
local buoyancy or buoyancy proxy if available
local cap-relative cloud top if available
thermal-fate label, confidence, and caveats
comparison to domain diagnostics where available
```

The first implementation should not attempt full cloud-object tracking. Point,
column, and box summaries are enough to make `What happened here?` useful.

## Comparison Diagnostics

Comparison diagnostics should explain what changed between a baseline and a
variant.

Supported comparison pairs should include, as data becomes available:

```text
Baseline vs Dry Failed
Baseline vs More Humid / Drier
Baseline vs Capped / Suppressed
Baseline vs Stronger Heating
Warm Patch vs Background Region
Shallow vs Deep Breakthrough Candidate
Before vs After Rain Onset
```

Comparison outputs should include:

```text
difference in first cloud time
difference in max qc
difference in max/min w
difference in cloud-top time series
difference in cloud fraction
difference in rain onset / qr summary
difference in thermal-fate label/confidence
main changed control or scenario factor
caveats / missing fields
```

## User-Facing Process Modes

Explore should eventually expose process modes or overlays such as:

```text
Thermal Fate
Cloud Water
Updrafts
Moisture / Saturation
Buoyancy
Cap / Inversion
Cloud Lifecycle
Deep Breakthrough
Precipitation Feedback
Baseline vs Dry Failed
Baseline vs Capped
Baseline vs Stronger Heating
Shallow vs Deep Convection
```

The main UI should present atmospheric concepts first. Raw CM1 field names belong
in technical details.

## Explanation Contract

Explanations must be driven by diagnostics and caveats, not hardcoded story
beats.

Good supported explanations:

```text
This dry case still produced meaningful vertical motion, but qc stayed below the cloud threshold. The result supports a moisture-limited no-cloud interpretation rather than a failed simulation.

Cloud formed at 1800 s as qc exceeded the cloud threshold near the diagnosed cloud-base layer.

Compared with nearby shallow clouds, this selected region maintained stronger upward motion above cloud base and its cloud top rose across several output times.

Updrafts remained active below the cloud, but cloud top stayed below the stronger cap. Compared with baseline, max qc and cloud fraction were lower.

Rain water appeared after the cloud deepened. After rain onset, a downdraft developed below the rain shaft.
```

Good caveated explanations:

```text
Available diagnostics are consistent with dilution / evaporation near the cloud edge, but direct entrainment is not diagnosed in this view.

Deep-breakthrough diagnostics are not available for this result because LFC/CAPE metadata was not generated.

Cold-pool diagnostics are unavailable because near-surface theta-v perturbation and outflow proxies were not ingested.
```

Bad explanations:

```text
The cloud died from entrainment.
This became cumulonimbus.
The cold pool triggered the next storm.
```

unless the supporting fields and diagnostics satisfy the relevant criteria.

## Data And API Contract Direction

Process diagnostics should live with result metadata and visualization-ready APIs.
The exact schema can evolve, but it should preserve these concepts:

```json
{
  "process_diagnostics": {
    "thermal_fate": {},
    "cloud_lifecycle": {},
    "updrafts": {},
    "moisture_saturation": {},
    "cap_inversion": {},
    "buoyancy": {},
    "deep_breakthrough": {},
    "precipitation_feedback": {},
    "local_region_support": {},
    "interpretation_support": {
      "main_limiting_factor": "moisture | cap/stability | surface_heating | dry_air_aloft | precipitation_feedback | unknown",
      "thermal_fate_label": "...",
      "confidence": "supported | candidate | insufficient_evidence | unsupported_missing_fields",
      "caveats": []
    }
  }
}
```

Selected-region APIs should return bounded summaries, not large raw arrays.
Backend code owns NetCDF/xarray access, field selection, coordinate handling,
downsampling, and diagnostic derivation.

## Testing Contract

Thermal Fate tests should use tiny synthetic fixtures and temporary runtime
homes. CI must not run real CM1 or require local output.

Backend tests should cover:

```text
thermal-fate labels
supported / candidate / insufficient-evidence / unsupported-missing-fields states
global process diagnostics
selected-region diagnostics
comparison diagnostics
missing fields
non-finite fields
serialization round trips
API payload shapes
deep-breakthrough unavailable/candidate/supported states
precipitation-feedback unavailable/candidate/supported states
surface-heating scenario metadata and package generation
```

Frontend tests should cover:

```text
process mode / overlay selection
available and unavailable diagnostics
thermal-fate label display
confidence/caveat display
selected-region inspector states
backend failure states
technical details expansion
Results -> Explore selected-result flow
```

Manual QA should focus on qualitative scientific trust:

```text
Does the explanation teach the right lesson?
Does the selected-region inspector feel like `What happened here?`
Are caveats clear but not overwhelming?
Does the visualization feel physically believable?
Does the UI avoid implying unsupported causality?
```

## Implementation Sequence

Recommended sequence after the baseline/capped CM1 path is stable:

```text
#148 Thermal Fate Framework / process contract
-> #149 global/process diagnostics
-> #151 selected-region backend diagnostics
-> #150 Thermal Fate overlays in Explore
-> #152 Thermal Fate Inspector UI
-> #153 surface-heating scenario family
-> #154 deep-convection breakthrough scenario family
-> #155 precipitation feedback / cold-pool scenario family
-> #112 renderer upgrade after process needs are clear
```

Renderer polish should remain downstream of process diagnostics and selected-region
inspection needs.

## Non-Goals

This contract does not require immediate implementation of every diagnostic.
It defines the product/science architecture so implementation can be staged.

Do not:

- run CM1 in CI;
- commit generated CM1 output;
- invent thermal-fate labels without diagnostic support;
- claim direct entrainment, deep breakthrough, or cold-pool causality from weak
  proxies;
- build arbitrary surface-heating maps before curated scenarios are trustworthy;
- choose renderer upgrades before process needs are defined.
