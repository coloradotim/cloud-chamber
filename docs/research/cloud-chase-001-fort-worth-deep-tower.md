# Cloud Chase 001: Deep-Tower Benchmark

Issue: #348  
Implementation vehicle: #341

## Recipe Setup

- Recipe: `deep_tower_benchmark_v0`.
- Initiation: stock CM1 `iinit = 3`, the built-in three-warm-bubble line trigger.
- Lower boundary: surface heat and moisture fluxes disabled.
- Domain/run shape: 120 km by 120 km, 120 by 120 horizontal cells, 40 vertical levels, 20 km model top, 2 hour scout, 15 minute output cadence, 6 s time step.

This was an explicit thermal-initiation experiment. It does not claim a real
front, dryline, outflow boundary, terrain trigger, or forecast initialization.

## Attempts

1. The legacy `triggered_deep_potential` path failed closed because that package
   generator had been removed from the current architecture.
2. Restoring the Deep-Tower Benchmark path through #341 produced one real CM1
   run: `cloud_chase_001-fort_worth_deep_tower_probe`.
3. The existing sounding analyzer was broadened beyond the short initial cache
   and used to select a non-Aberdeen high-potential comparison case:
   `cloud_chase_001-north_platte_high_potential`.
4. A marginal/capped comparison package was created but not launched after the
   North Platte run showed low compute value:
   `cloud_chase_001-rapid_city_marginal_capped`.

## Best Result

Fort Worth, TX, `USM00072249`, `1997-05-27T00:00:00Z`.

- CM1 completed normally with 9 model-output NetCDF frames from 0 to 7200 s.
- Ingest completed with no missing required output fields.
- Remaining runtime warning: `IEEE_UNDERFLOW_FLAG`.
- Diagnostic summary: cloud formed, rain water aloft detected, surface rain
  reached ground, reflectivity available.
- First cloud: 900 s.
- First deep convection: 1800 s.
- Highest coherent cloud-object top: 17,250 m.
- Highest hydrometeor envelope top: 19,750 m.
- Highest liquid cloud-water top: 10,750 m.
- Maximum updraft: 54.13 m/s at 1800 s.
- Minimum downdraft: -15.89 m/s at 1800 s.
- Maximum cloud water: 0.005071 kg/kg.
- Maximum rain water aloft: 0.006555 kg/kg.
- Maximum surface rainfall accumulation: 0.721 cm.
- Maximum reflectivity: 65.38 dBZ.

Visual-interest rating: 5/5.  
Compute value: high. The scout produced a clear, inspectable deep-convective
result by 1800 s.

## Comparison Run

North Platte, NE, `USM00072562`, `2026-07-02T00:00:00Z`.

Analyzer expectation:

- Selection: top non-Aberdeen candidate from the broadened
  `deep_convection_trial` target-story ranking.
- Story: severe thunderstorm environment.
- Rank score: 62.6.
- Summary: some deep-convection ingredients are present, but evidence is
  caveated.

Actual outcome:

- Run stopped at user request after eight model-output frames through 6300 s.
- No coherent cloud formed by the product threshold.
- Coherent cloud top: unavailable.
- Trace raw/liquid hydrometeor envelope appeared briefly near 1750 m at 900 s,
  but did not meet coherent cloud-object support.
- Maximum cloud water: 8.36e-5 kg/kg at 900 s.
- Maximum updraft: 0.86 m/s at 900 s.
- Rain water aloft: none.
- Surface rain: none.
- Reflectivity: field available, no meaningful signal.
- Runtime integrity: partial output was finite and interpretable.

Visual-interest rating: 1/5.  
Compute value: low. The run was numerically useful enough to reject the setup,
but it was not worth completing once the weak response persisted past 6300 s.

## Canceled Contrast Package

Rapid City WFO, SD, `USM00072662`, `2026-07-15T00:00:00Z`.

Analyzer expectation:

- Selection: low-score weak capped/suppressed package-ready candidate from the
  broadened analyzer pool.
- Active story: capped / suppressed cumulus candidate.
- Active-story score: 35.0, weak support.
- Summary: dry-layer signal could matter for entrainment or downdraft behavior.

The package was generated with the same Deep-Tower Benchmark settings but was
canceled before launch after the North Platte comparison showed that the next
product value was analyzer selection improvement, not another immediate CM1
run.

## What Worked

The Fort Worth environment responded strongly once explicit initiation was
supplied. The run produced a deep, intense convective result quickly enough for a
2 hour scout to be useful, and the core cloud, updraft, rain, reflectivity, wind,
theta, and CM1 `uh` updraft-helicity output were available for product
inspection.

## What Failed

The broader analyzer still pushed a scientifically plausible but visually poor
high-potential case. North Platte had enough moisture/shear proxy support to rank
high after excluding Aberdeen, but the same explicit Deep-Tower Benchmark
produced only a weak, shallow, transient response.

## Product Recommendation

Keep Deep-Tower Benchmark as a repeatable Build recipe, but improve the analyzer
before spending more CM1 runs: down-rank known-boring stations/cases from prior
Deep-Tower outcomes and require stronger deep-instability evidence than moisture
and shear proxies alone before labeling a case high-potential. Build should
still label the recipe as explicit initiation and keep surface-forced and
observed-boundary initiation recipes separate.
