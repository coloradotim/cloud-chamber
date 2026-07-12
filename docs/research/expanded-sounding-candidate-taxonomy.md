# Expanded Sounding Candidate Taxonomy

Status: draft product/science taxonomy

This document defines future real-sounding candidate stories before Cloud
Chamber exposes more story labels in Build. It is a planning and readiness
contract, not an implementation of new scoring, UI filters, or CM1 package
families.

CM1 output remains the source of truth. Candidate labels are pre-run
hypotheses that help a user choose an observed atmosphere to try. A sounding
can be scientifically interesting even when the current observed-sounding
package is only a caveated way to test it.

## Product Rules

- Do not present all candidate stories as equally runnable.
- Do not imply that a screening label predicts CM1 output.
- Do not add visible story labels until backend scoring, evidence, caveats, and
  package readiness can support them.
- Keep the browser out of raw IGRA station text, ZIP archives, and NetCDF.
- Keep the current observed-sounding package honest: it can run a converted
  external sounding, but it is not a specialized severe-storm, winter-weather,
  fog, or cold-pool package.

## Readiness Fields

Every story in this taxonomy declares these fields:

| Field | Values | Meaning |
| --- | --- | --- |
| `screenable_from_sounding_now` | `yes`, `no`, `later` | Whether current backend features can screen this story from cached sounding text. |
| `runnable_with_current_observed_sounding_package` | `yes`, `caveated`, `no` | Whether the current observed-sounding package can run a meaningful first experiment for the story. |
| `specialized_package_recommended` | `yes`, `no` | Whether a future package should better represent the story physics. |
| `future_package_required` | `yes`, `no` | Whether the story should be blocked from package generation until a new package family exists. |
| `candidate_can_be_saved` | `yes`, `no` | Whether the UI may save this candidate as a pre-run hypothesis. |
| `candidate_can_generate_current_package` | `yes`, `caveated`, `no` | Whether `Configure run` may use this candidate for the current observed-sounding package path. |

The UI should map these fields to simple readiness states:

- **Package-ready now**: supported story and current observed-sounding package is appropriate.
- **Runnable as current observed-sounding experiment, caveated**: the sounding can be run now, but the story needs caveats because the package is not specialized.
- **Specialized package recommended**: saving and inspection may be useful, but package generation should explain the mismatch.
- **Future package needed**: do not generate a current package for this story.
- **Blocked**: source data are incomplete or unsafe for package generation.

## Current Observed-Sounding LES Stories

These stories remain current-package oriented. Their scoring inputs, evidence
fields, and missing-data rules are defined by
[Sounding Candidate Screening Contract](../contracts/sounding-candidate-screening.md).
They are still subject to audit and calibration as real runs accumulate.

| Story ID | Visible Label | Family | screenable_from_sounding_now | runnable_with_current_observed_sounding_package | specialized_package_recommended | future_package_required | candidate_can_be_saved | candidate_can_generate_current_package | Implementation Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `shallow_cumulus_candidate` | Cloud-forming shallow cumulus | Current observed-sounding LES stories | yes | yes | no | no | yes | yes | current |
| `dry_failed_candidate` | Dry failed cumulus | Current observed-sounding LES stories | yes | yes | no | no | yes | yes | current |
| `capped_suppressed_candidate` | Capped / suppressed | Current observed-sounding LES stories | yes | caveated | yes | no | yes | caveated | current, needs calibration |
| `humid_rainy_candidate` | Humid / rainy | Current observed-sounding LES stories | yes | caveated | yes | no | yes | caveated | current, needs calibration |
| `needs_review` | Needs review | Review | yes | caveated | no | no | yes | caveated | current |
| `poor_or_incomplete_candidate` | Poor or incomplete data | Review | yes | no | no | no | yes | no | current |

### Cloud-Forming Shallow Cumulus

Story goal: find observed lower-atmosphere profiles that may support shallow
cumulus in the current LES package.

Plain-language explanation: moisture and thermals look plausible enough to try
a shallow-cumulus run.

Required features: package-ready observed sounding, usable thermodynamic
profile, usable observed winds, low-order moisture and stability features from
the current contract.

Candidate evidence: mean qv 0-1000 m, estimated LCL, low-level lapse rate,
moisture depth, cap proxy, completeness, and caveats.

Candidate caveats: current package uses idealized local forcing; candidate
score is not a cloud forecast.

Result comparison target: first cloud time, max cloud water, cloud top, cloud
fraction, max/min vertical velocity, rain onset, and caveats.

Non-goals: do not infer storm mode, precipitation process, or real-world
weather outcome from this story.

### Dry Failed Cumulus

Story goal: find profiles where thermals may exist but cloud water may remain
limited by low moisture or high cloud base.

Plain-language explanation: the atmosphere may be too dry for meaningful
cloud, even if vertical motion develops.

Required features: package-ready observed sounding, usable qv/LCL/moisture-depth
features, usable observed winds.

Candidate evidence: low mean qv 0-1000 m, higher estimated LCL, shallow
moisture depth, low-level lapse rate, dry-layer proxy, and completeness.

Candidate caveats: missing moisture is not dry air; no-cloud remains a CM1
outcome, not a candidate guarantee.

Result comparison target: no or weak cloud water, meaningful vertical velocity,
rain absent, finite target fields, and explanation of moisture limitation.

Non-goals: do not tune moisture in this taxonomy; implementation belongs in
package/science issues.

### Capped / Suppressed

Story goal: find profiles where moisture and thermals may be present but a
stable layer may limit vertical growth.

Plain-language explanation: the atmosphere may have a stronger lid.

Required features: package-ready observed sounding, usable cap-strength proxy,
usable moisture and LCL features, usable observed winds.

Candidate evidence: cap strength proxy, cap height context, mean qv 0-1000 m,
estimated LCL, low-level lapse rate, moisture depth, and completeness.

Candidate caveats: current scoring does not prove cap-limited growth; current
package may need a specialized stronger-cap variant for cleaner comparison.

Result comparison target: lower cloud top, reduced cloud fraction or max qc,
delayed first cloud time, meaningful vertical velocity below the cap, and rain
reduced or absent relative to baseline.

Non-goals: do not expose cap-height controls or new package families from this
taxonomy alone.

### Humid / Rainy

Story goal: find moist lower-atmosphere profiles worth trying when the user
wants stronger cloud or rain behavior.

Plain-language explanation: the sounding is moist and low-cloud-base enough to
try, but CM1 decides whether rain actually forms.

Required features: package-ready observed sounding, usable low-level moisture,
LCL, cap proxy, and wind profile.

Candidate evidence: high mean qv 0-1000 m, low estimated LCL, deep moisture,
weak cap proxy, completeness, and package readiness.

Candidate caveats: the current package is not a precipitation-tuned package,
and the score is not a rain forecast.

Result comparison target: rain onset, accumulated rain if available, qr/dbz
fields when present and trustworthy, max qc, cloud top, vertical velocity, and
precipitation caveats.

Non-goals: do not treat radar reflectivity, surface rain, or precipitation
feedback as validated until output products and diagnostics support them.

### Needs Review

Story goal: preserve interesting or ambiguous candidates without pretending a
specific story is supported.

Plain-language explanation: the sounding may be worth looking at, but the
screening evidence is incomplete or mixed.

Required features: enough data to display a candidate; package generation may
still depend on package-readiness checks.

Candidate evidence: available moisture, LCL, stability, wind, profile coverage,
and package-readiness context.

Candidate caveats: weak evidence, missing story-driving fields, or mixed story
support.

Result comparison target: depends on the story the user chooses after review.

Non-goals: do not use `needs_review` as a hidden failure bucket when the
candidate should be explicitly blocked.

### Poor Or Incomplete Data

Story goal: explain why a sounding cannot safely generate the current package.

Plain-language explanation: the source profile is not usable enough for a CM1
package without parser, metadata, or data-quality improvements.

Required features: none beyond enough source metadata to identify the blocked
candidate.

Candidate evidence: missing elevation, too few levels, profile top too low,
lowest usable level too high, nonmonotonic or nonfinite fields, or missing
observed winds.

Candidate caveats: blocked candidates may become useful after better metadata
or parser support.

Result comparison target: none until package generation is unblocked.

Non-goals: do not allow package generation from blocked candidates.

## Deep Convection / Severe Environments

These stories are first-class product concepts, but they are not current
package-ready stories. Most require thermodynamic and wind diagnostics that are
not part of the current candidate scoring contract, such as CAPE, CIN, LFC,
EL, 0-6 km shear, storm-relative helicity, DCAPE, freezing-level diagnostics,
or forcing/cold-pool architecture.

| Story ID | Visible Label | Family | screenable_from_sounding_now | runnable_with_current_observed_sounding_package | specialized_package_recommended | future_package_required | candidate_can_be_saved | candidate_can_generate_current_package | Implementation Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `severe_thunderstorm_environment` | Severe thunderstorm environment | Deep-convection environments | later | caveated | yes | no | yes | caveated | high future |
| `supercell_environment` | Supercell environment | Deep-convection environments | later | no | yes | yes | yes | no | high future |
| `high_cape_pulse_storm` | High-CAPE pulse storm | Deep-convection environments | later | caveated | yes | no | yes | caveated | medium future |
| `squall_line_cold_pool_candidate` | Squall line / cold-pool candidate | Deep-convection environments | later | no | yes | yes | yes | no | medium future |
| `elevated_convection` | Elevated convection | Deep-convection environments | later | no | yes | yes | yes | no | medium future |
| `dry_microburst_inverted_v` | Dry microburst / inverted-V | Deep-convection environments | later | caveated | yes | no | yes | caveated | medium future |

### Severe Thunderstorm Environment

Story goal: identify observed soundings with ingredients that may support deep
convection once Cloud Chamber has deep-convection diagnostics and package
families.

Plain-language explanation: instability, moisture, and wind structure may make
this an interesting severe-storm environment, but Cloud Chamber cannot yet run
a validated severe-storm package.

Required sounding features: CAPE, CIN, LCL, LFC, EL, deep-layer shear,
low-level shear or SRH, moisture depth, freezing-level context, and package
quality.

Optional supporting features: lapse rates aloft, dry air aloft, DCAPE,
precipitable water, hodograph shape, and storm-mode caveats.

Candidate evidence fields: CAPE/CIN/LFC/EL, 0-6 km shear, 0-1 km shear/SRH,
LCL, lapse rates, moisture, dry layer, and completeness.

Candidate caveats: sounding-only screening cannot prove initiation, storm
mode, tornado potential, hail, or precipitation outcome.

Package readiness: current observed-sounding package can only provide a
caveated exploratory run from the profile. A specialized deep-convection
package is recommended before this becomes a validated severe-environment
story.

Result/outcome comparison target: deep updraft, cloud depth, precipitation,
gust-front or cold-pool evidence if a future package supports it, and whether
the simulated storm behavior matches the severe-environment hypothesis.

Non-goals: no tornado, hail-size, warning, or forecast claims.

### Supercell Environment

Story goal: find soundings with buoyancy and shear profiles that may support
organized rotating convection in a future specialized package.

Plain-language explanation: the wind and instability profile may favor a
rotating storm, but the current package is not a supercell simulator.

Required sounding features: CAPE/CIN/LFC/EL, 0-6 km shear, low-level shear,
SRH or hodograph-derived metrics, LCL, and storm-relative wind assumptions.

Optional supporting features: effective shear, effective inflow layer,
midlevel lapse rate, dry air aloft, and storm-motion sensitivity.

Candidate evidence fields: shear/SRH diagnostics, CAPE/CIN, LCL, LFC/EL,
hodograph summary, moisture depth, and caveats.

Candidate caveats: supercell potential depends on initiation, forcing, storm
motion, and model configuration; current Cloud Chamber does not compute or
validate that package.

Package readiness: future package required; do not generate the current package
as if it were a supercell case.

Result/outcome comparison target: future rotating updraft diagnostics, storm
organization, precipitation/cold-pool interactions, and provenance caveats.

Non-goals: no tornado prediction and no severe-weather forecast product.

### High-CAPE Pulse Storm

Story goal: identify high-instability, weaker-shear profiles for future
ordinary deep-convection experiments.

Plain-language explanation: the atmosphere may support strong buoyant updrafts
without a clear organized-storm wind profile.

Required sounding features: CAPE, CIN, LFC/EL, LCL, midlevel lapse rate,
moisture depth, and deep-layer shear to distinguish pulse from organized storm
stories.

Optional supporting features: precipitable water, freezing level, dry air
aloft, and DCAPE.

Candidate evidence fields: CAPE/CIN, LCL/LFC/EL, lapse rates, shear, moisture,
and completeness.

Candidate caveats: current packages are shallow-LES oriented; a high-CAPE
candidate may run but should not be represented as a validated deep-convection
experiment.

Package readiness: caveated current-package generation may be useful for
profile exploration, but a future deep-convection package is recommended
before this becomes a validated high-CAPE pulse-storm story.

Result/outcome comparison target: future deep cloud depth, updraft strength,
precipitation, and whether convection remains pulse-like.

Non-goals: no storm initiation or storm lifecycle promise.

### Squall Line / Cold-Pool Candidate

Story goal: identify profiles that may support cold-pool-driven organized
convection once Cloud Chamber has line forcing, precipitation, and cold-pool
diagnostics.

Plain-language explanation: the profile may be favorable for organized storms
with precipitation-driven outflow, but a single sounding is not enough to run a
validated squall-line case.

Required sounding features: CAPE/CIN, deep shear, low-level shear, moisture
depth, precipitation/cold-pool potential, DCAPE, and environmental wind profile.

Optional supporting features: boundary/forcing metadata, storm motion,
precipitable water, and low-level theta-e gradients if available.

Candidate evidence fields: CAPE/CIN, shear, moisture, DCAPE, lapse rates,
freezing level, and caveats.

Candidate caveats: cold-pool behavior is an output and package-design problem;
it cannot be proven from sounding metadata alone.

Package readiness: future package required; current package generation should
be blocked for this story label.

Result/outcome comparison target: future precipitation, downdrafts, surface
cooling, outflow depth, gust-front propagation, and organized line behavior.

Non-goals: no precipitation/cold-pool scenario implementation here.

### Elevated Convection

Story goal: identify profiles where instability is rooted above a stable
surface layer.

Plain-language explanation: storms or clouds may be fed by air above the
surface, so a surface-based shallow package is the wrong experiment.

Required sounding features: elevated unstable layer, stable boundary layer,
elevated LFC, CIN below inflow layer, moisture above the surface, and wind
profile through the elevated layer.

Optional supporting features: frontal or isentropic lift metadata if available,
low-level jet, and nocturnal timing context.

Candidate evidence fields: layer-specific CAPE/CIN, stable-layer depth,
elevated moisture, LFC/LCL, and wind profile.

Candidate caveats: forcing and elevated inflow are not represented by the
current observed-sounding package.

Package readiness: future package required.

Result/outcome comparison target: future elevated cloud/updraft source layer,
surface decoupling, precipitation onset, and caveats about forcing.

Non-goals: no implied initiation from sounding-only evidence.

### Dry Microburst / Inverted-V

Story goal: identify inverted-V profiles that may support strong evaporative
downdrafts in future precipitation-capable experiments.

Plain-language explanation: dry subcloud air may make downdrafts interesting
if precipitation forms aloft.

Required sounding features: dry low-level layer, high cloud base or inverted-V
shape, moisture aloft, lapse rate, DCAPE or downdraft proxy, and enough upper
profile coverage.

Optional supporting features: precipitation potential aloft, boundary-layer
depth, surface temperature/dewpoint spread, and wind profile.

Candidate evidence fields: T-Td spread, LCL, dry-layer depth, moisture aloft,
DCAPE/downdraft proxy, lapse rates, and completeness.

Candidate caveats: microbursts require precipitation and evaporative cooling;
the current package does not validate that pathway.

Package readiness: current observed-sounding generation is caveated for profile
exploration only; a future precipitation/downdraft package is recommended
before this becomes a validated dry-microburst story.

Result/outcome comparison target: future precipitation aloft, downdraft
strength, evaporative cooling, near-surface outflow, and caveats.

Non-goals: no operational wind-gust prediction.

## Boundary-Layer / Low-Cloud Environments

These stories are closer to LES than the deep-convection families, but most
need radiation, surface-flux, land, or advection controls that are not yet
validated in the current observed-sounding package.

| Story ID | Visible Label | Family | screenable_from_sounding_now | runnable_with_current_observed_sounding_package | specialized_package_recommended | future_package_required | candidate_can_be_saved | candidate_can_generate_current_package | Implementation Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stable_nocturnal_boundary_layer` | Stable / nocturnal boundary layer | Boundary-layer / low-cloud | later | no | yes | yes | yes | no | high future |
| `fog_stratus_candidate` | Fog / stratus candidate | Boundary-layer / low-cloud | later | no | yes | yes | yes | no | medium future |
| `post_frontal_shallow_cumulus` | Post-frontal shallow cumulus | Boundary-layer / low-cloud | later | caveated | yes | no | yes | caveated | medium future |
| `cold_air_advection_boundary_layer` | Cold-air-advection boundary layer | Boundary-layer / low-cloud | later | no | yes | yes | yes | no | medium future |

### Stable / Nocturnal Boundary Layer

Story goal: identify stable near-surface profiles and nocturnal boundary-layer
structure for future radiation/surface-flux LES experiments.

Plain-language explanation: the lower atmosphere is stable or decoupled, so
daytime shallow-cumulus assumptions may be wrong.

Required sounding features: surface-based inversion, stable-layer depth,
low-level wind profile, moisture near the surface, and valid time/night context.

Optional supporting features: radiative cooling proxies, low-level jet,
station land context, and surface flux metadata.

Candidate evidence fields: inversion strength, inversion depth, low-level
lapse rate, wind shear, qv/RH near surface, valid time, and caveats.

Candidate caveats: current package lacks nocturnal radiation and stable
surface-flux controls.

Package readiness: future package required.

Result/outcome comparison target: future boundary-layer depth, turbulence,
mixing, wind shear, near-surface cooling, and cloud/fog presence if applicable.

Non-goals: no stable-boundary-layer UI until radiation/surface handling is
validated.

### Fog / Stratus Candidate

Story goal: identify moist, stable, low-cloud profiles that may support fog or
stratus in future low-cloud packages.

Plain-language explanation: the near-surface air is moist and stable enough
that fog or stratus may be interesting.

Required sounding features: near-surface saturation or small T-Td spread,
stable layer, low cloud base, sufficient vertical resolution near the surface,
and valid time context.

Optional supporting features: radiation, surface moisture, wind speed, land or
water context, and cloud-layer depth.

Candidate evidence fields: T-Td spread, RH/qv near surface, LCL, stable-layer
depth, wind speed, and caveats.

Candidate caveats: fog/stratus depends strongly on radiation and surface
conditions, which the current package does not represent.

Package readiness: future package required.

Result/outcome comparison target: future liquid water near the surface, cloud
base, fog/stratus layer depth, turbulence, and dissipation timing.

Non-goals: no aviation visibility or operational fog forecast.

### Post-Frontal Shallow Cumulus

Story goal: identify cool, mixed, modestly moist profiles that may support
post-frontal shallow cumulus.

Plain-language explanation: cold air over a warmer or recovering surface may
produce shallow cloud streets or low cumulus.

Required sounding features: low-level instability or steep lapse rate, modest
moisture, low-to-moderate LCL, wind profile, and post-frontal context if
available.

Optional supporting features: cold-advection metadata, surface fluxes,
boundary-layer depth, and cloud-top inversion.

Candidate evidence fields: low-level lapse rate, qv, LCL, cap/inversion
context, wind, valid time, and caveats.

Candidate caveats: advection and surface state are not fully represented by
the current observed-sounding package.

Package readiness: current package generation is caveated; a future
post-frontal package may better capture the story.

Result/outcome comparison target: shallow cloud timing, cloud-top height,
updraft strength, cloud streets if future domain/wind handling supports them,
and rain absence.

Non-goals: no synoptic frontal analysis in current screening.

### Cold-Air-Advection Boundary Layer

Story goal: identify cold-advection environments where surface forcing and
mixing may produce distinctive boundary-layer evolution.

Plain-language explanation: the lower atmosphere may be changing because air is
moving over a different surface, not just because of local heating.

Required sounding features: cold low-level profile, mixed-layer depth, wind
profile, stability, and external advection/surface context.

Optional supporting features: upstream/downstream station comparison, surface
temperature contrast, water/land context, and radiation.

Candidate evidence fields: temperature profile, lapse rate, wind, moisture,
surface context, and caveats.

Candidate caveats: advection is not a single-sounding feature and is not
represented by current package generation.

Package readiness: future package required.

Result/outcome comparison target: future boundary-layer growth, mixing,
cloud streets or shallow cloud formation, and surface flux sensitivity.

Non-goals: no GIS/map or arbitrary location controls from this taxonomy alone.

## Winter / Cold-Season Future Stories

These are captured so future planning does not lose the product direction, but
they are research/future stories. They require thermodynamic phase, hydrometeor,
surface, radiation, and often mesoscale-forcing decisions that are outside the
current LES bench.

| Story ID | Visible Label | Family | screenable_from_sounding_now | runnable_with_current_observed_sounding_package | specialized_package_recommended | future_package_required | candidate_can_be_saved | candidate_can_generate_current_package | Implementation Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `winter_weather_candidate` | Winter weather candidate | Winter / cold-season future | later | no | yes | yes | yes | no | future research |
| `freezing_rain_warm_nose_candidate` | Freezing rain / warm nose | Winter / cold-season future | later | no | yes | yes | yes | no | future research |
| `snow_squall_candidate` | Snow squall | Winter / cold-season future | later | no | yes | yes | yes | no | future research |
| `thundersnow_candidate` | Thundersnow | Winter / cold-season future | later | no | yes | yes | yes | no | future research |
| `lake_effect_candidate` | Lake-effect candidate | Winter / cold-season future | later | no | yes | yes | yes | no | future research |
| `cold_stable_boundary_layer` | Cold stable boundary layer | Winter / cold-season future | later | no | yes | yes | yes | no | future research |

### Winter Weather Candidate

Story goal: preserve a broad future category for cold-season profiles before
Cloud Chamber has phase-aware packages and output products.

Plain-language explanation: the profile has cold-season structure that may be
interesting later, but current packages are not winter-weather experiments.

Required sounding features: temperature profile relative to freezing, moisture,
cloud/precipitation layer proxies, wind profile, and surface temperature.

Optional supporting features: snow growth zone, warm nose, wet-bulb
temperature, lift/forcing context, and surface metadata.

Candidate evidence fields: temperature, dewpoint, wet-bulb or RH, freezing
level, wind, and caveats.

Candidate caveats: phase and precipitation type require more than current
candidate screening.

Result/outcome comparison target: future hydrometeor phase, precipitation
location, cloud depth, and surface-temperature response.

Non-goals: no winter precipitation-type forecast.

### Freezing Rain / Warm Nose

Story goal: identify warm-layer-over-cold-surface profiles for future
phase-aware experiments.

Plain-language explanation: a warm layer aloft over subfreezing near-surface
air may support freezing-rain processes in a future package.

Required sounding features: above-freezing warm nose, subfreezing surface
layer, saturation/moisture in precipitation layer, wet-bulb profile, and
surface temperature.

Optional supporting features: precipitation/lift context, layer thickness,
wind, and surface heat budget.

Candidate evidence fields: warm-nose depth and temperature, cold-layer depth,
wet-bulb profile, RH, and caveats.

Candidate caveats: precipitation presence and phase are not determined by the
current package.

Result/outcome comparison target: future hydrometeor phase, melting/refreezing
layers, surface cold-layer evolution, and caveats.

Non-goals: no operational icing forecast.

### Snow Squall

Story goal: identify convective snow environments for future shallow/deep
cold-season packages.

Plain-language explanation: cold instability and wind may make a short-lived
convective snow environment interesting.

Required sounding features: low-level instability, subfreezing profile,
moisture, wind/shear, snow growth zone context, and surface forcing.

Optional supporting features: frontal forcing, lake/land contrast, and
precipitation context.

Candidate evidence fields: lapse rates, temperature, moisture, wind,
snow-growth-layer metrics, and caveats.

Candidate caveats: squall organization requires forcing and microphysics
choices outside current packages.

Result/outcome comparison target: future snow hydrometeor fields, updrafts,
visibility proxy if defined, and surface response.

Non-goals: no travel-impact or visibility product.

### Thundersnow

Story goal: identify rare cold-season profiles with instability and
precipitation-layer support for future research.

Plain-language explanation: a winter profile may have enough instability aloft
to make electrified or convective snow worth studying later.

Required sounding features: elevated or deep instability, saturated cold cloud
layer, freezing profile, wind/shear, and forcing context.

Optional supporting features: charge-region proxies if ever defined, high
precipitation intensity proxies, and lift metadata.

Candidate evidence fields: CAPE aloft, temperature, moisture, LFC/EL,
snow-growth-zone context, and caveats.

Candidate caveats: electrification is not a current Cloud Chamber diagnostic.

Result/outcome comparison target: future deep cold cloud, updrafts,
precipitation intensity, and caveats.

Non-goals: no lightning or electrification forecast.

### Lake-Effect Candidate

Story goal: identify profiles where cold air over warmer water could support
lake-effect convection in future surface/land-water packages.

Plain-language explanation: the atmosphere may be favorable for lake-effect
cloud or snow, but a water-surface fetch and surface-flux setup are required.

Required sounding features: cold air over water context, low-level instability,
moisture, wind direction/speed, inversion height, and surface-water
temperature or proxy.

Optional supporting features: fetch, upstream moisture, snow-growth layer, and
boundary-layer depth.

Candidate evidence fields: inversion height, lapse rate, moisture, wind, lake
surface context, and caveats.

Candidate caveats: GIS/surface context is essential and not part of current
observed-sounding package generation.

Result/outcome comparison target: future banded cloud/snow, boundary-layer
growth, surface flux sensitivity, and precipitation.

Non-goals: no map/GIS input implementation here.

### Cold Stable Boundary Layer

Story goal: represent cold, stable near-surface profiles separately from warmer
nocturnal stable cases.

Plain-language explanation: the lower atmosphere is cold and stable, with
limited mixing unless surface or radiation forcing changes.

Required sounding features: subfreezing near-surface temperature, stable layer,
wind profile, moisture, and valid time/source context.

Optional supporting features: snow cover, radiation, surface flux, and land
metadata.

Candidate evidence fields: temperature, inversion strength, wind, qv/RH,
profile depth, and caveats.

Candidate caveats: surface state and radiation dominate; current package is
not a cold-stable-boundary-layer experiment.

Result/outcome comparison target: future near-surface temperature, turbulence,
mixing depth, fog/stratus/ice-cloud presence, and caveats.

Non-goals: no cold-weather forecast or surface-energy-budget claim.

## UI Grouping Recommendation

Build should group story filters by readiness, not alphabetically as if all
stories were equivalent.

```text
Current observed-sounding LES stories
  Cloud-forming shallow cumulus
  Dry failed cumulus
  Capped / suppressed
  Humid / rainy
  Stable / nocturnal boundary layer, if implemented later

Deep-convection environments
  Severe thunderstorm environment
  Supercell environment
  High-CAPE pulse storm
  Elevated convection
  Dry microburst / inverted-V
  Squall line / cold-pool candidate

Boundary-layer / low-cloud
  Stable / nocturnal boundary layer
  Fog / stratus candidate
  Post-frontal shallow cumulus
  Cold-air-advection boundary layer

Winter / cold-season - future
  Winter weather candidate
  Freezing rain / warm nose
  Snow squall
  Thundersnow
  Lake-effect
  Cold stable boundary layer

Review
  Needs review
  Poor or incomplete data
```

When non-current stories appear in a future UI, the UI must show one of:

- `Package-ready now`
- `Runnable with current package, caveated`
- `Specialized package recommended`
- `Future package needed`
- `Blocked`

The UI must not let a severe, winter, or cold-pool label look like a current
package-ready shallow-LES story.

## Implementation Sequencing

1. Keep the current candidate stories governed by
   [Sounding Candidate Screening Contract](../contracts/sounding-candidate-screening.md).
2. Add feature products before new story scoring: CAPE, CIN, LFC, EL, shear,
   SRH, DCAPE, wet-bulb/freezing-level, stable-layer depth, and relevant
   caveats.
3. Add backend scoring for one future family at a time with tiny fixtures and
   explicit readiness states.
4. Add UI grouping only after the backend returns the grouping/readiness fields.
5. Add specialized CM1 package families only after a separate physical question,
   package contract, diagnostics, and validation plan exist.

## Non-Goals

- Do not implement severe/deep-convection scoring in this taxonomy.
- Do not implement CAPE, CIN, SRH, DCAPE, winter phase, or wet-bulb
  diagnostics here.
- Do not implement new CM1 package families here.
- Do not add enabled Build UI labels from this document alone.
- Do not run CM1.
- Do not make live NOAA/NCEI calls.
- Do not commit generated IGRA, CM1, NetCDF, runtime, screenshot, video, trace,
  or log artifacts.
