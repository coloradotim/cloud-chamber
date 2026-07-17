# Cloud Chase 003: Deep-Tower Opportunity Calibration

Issue: #351

## Goal

Improve the analyzer's answer to one recipe-specific question:

> Which observed soundings are worth spending a Deep-Tower Benchmark scout on?

This does not replace the existing severe/supercell story scores. Those remain
broader sounding hypotheses. The new `deep_tower_opportunity` field is narrower:
it scores whether the observed thermodynamic profile looks worth testing with
the Deep-Tower Benchmark's explicit CM1 thermal trigger.

## Scoring Change

Analyzer version: `sounding-screening-v2`.

The score favors ingredients that actually decide the cloud-depth question for
the benchmark trigger:

- surface-based and mixed-layer CAPE;
- CIN, LFC, and cap proxy;
- low-level moisture and deeper moisture;
- 0-3 km and midlevel lapse rates;
- profile completeness and near-surface continuity;
- EL or buoyancy depth only when the simple EL estimate is usable.

Deep-layer shear receives no positive weight in this recipe-specific score. It
remains useful for storm-organization stories, but Fort Worth versus North
Platte showed that shear can make a poor Deep-Tower Benchmark target look too
good.

## Outcome Evidence Compared

| Feature | Fort Worth success | North Platte miss |
| --- | ---: | ---: |
| Station / time | `USM00072249` / `1997-05-27T00:00:00Z` | `USM00072562` / `2026-07-02T00:00:00Z` |
| Surface-based CAPE | 1781.0 J/kg | 1081.7 J/kg |
| Mixed-layer CAPE | 1820.3 J/kg | 994.6 J/kg |
| Mixed-layer CIN | -5.3 J/kg | -1.7 J/kg |
| LFC | 2.8 m AGL | 0.2 m AGL |
| Mean qv 0-1 km | 20.398 g/kg | 14.83 g/kg |
| Mean qv 0-3 km | 14.623 g/kg | 11.052 g/kg |
| Moisture depth | 1893.8 m | 1542.2 m |
| Estimated LCL | 750.1 m AGL | 1225.1 m AGL |
| Cap proxy | 0.0 | 0.4 |
| 0-3 km lapse rate | 6.88 C/km | 8.09 C/km |
| Midlevel lapse rate | 7.97 C/km | 7.58 C/km |
| 0-6 km shear | 19.88 m/s | 22.39 m/s |
| Previous strongest deep story | 77.3 supported | 62.6 weak |
| `deep_tower_opportunity` | 81.7 supported | 46.1 weak |

The most plausible separators are CAPE, low-level/deep moisture, lower cloud
base, and absence of cap support. North Platte had stronger shear and steeper
low-level lapse-rate support, but those ingredients did not translate into a
coherent cloud under the benchmark trigger.

## Recommendation Trials

| Sounding | Analyzer version | Recipe / setup | Actual outcome |
| --- | --- | --- | --- |
| Fort Worth `USM00072249`, `1997-05-27T00:00:00Z` | `sounding-screening-v2` | `deep_tower_benchmark_v0`; stock CM1 `iinit = 3`; 120 km x 120 km; 120 x 120 x 40; 20 km model top; Rayleigh 15 km; 2 h; 15 min output; 6 s step; surface fluxes disabled | Success: coherent cloud top about 17.25 km, hydrometeor envelope about 19.75 km, max updraft 54.13 m/s, precipitation and 65.38 dBZ reflectivity, visual interest 5/5. |
| North Platte `USM00072562`, `2026-07-02T00:00:00Z` | `sounding-screening-v2` | Same Deep-Tower Benchmark setup; stopped after partial scout through 6300 s | Miss: no coherent cloud, no precipitation, max updraft about 0.86 m/s, visual interest 1/5. |
| Topeka `USM00072456`, `2026-06-10T00:00:00Z` | `sounding-screening-v2` | Same Deep-Tower Benchmark setup; completed 7200 s | Weak/shallow miss: shallow coherent cloud object only, no deep breakthrough. |

## New Candidate Selection

The revised analyzer scanned cached history with:

- `history_scope = all_cached`
- `story_family = deep_convection`
- `readiness = package_ready`
- `sort_by = best_match`

It analyzed 16,306 cached profiles and found 629 package-ready deep-family
candidates. The top remaining score after excluding the two executed outcomes
and Rapid City was a weak 55/100 tie between Aberdeen and Topeka. Topeka was
selected as the single new calibration scout because Aberdeen had already been
the explicitly skipped candidate in Cloud Chase 001; this is a tie-breaker for
new calibration value, not a station blacklist.

Selected candidate:

- Station: Topeka/Mun., KS, `USM00072456`.
- Valid time: `2026-06-10T00:00:00Z`.
- Predicted opportunity: 55.0/100, weak.
- Active story: dry microburst / inverted-V candidate, 54.3.
- Ingredients: SBCAPE 628.2 J/kg, MLCAPE 932.5 J/kg, qv 0-1 km 19.282 g/kg,
  qv 0-3 km 11.875 g/kg, moisture depth 1837.9 m, LCL 825.1 m, cap proxy 1.0.

## Topeka CM1 Result

Run: `cloud_chase_003-topeka_deep_tower_opportunity`.

Exact run shape:

- Recipe: `deep_tower_benchmark_v0`.
- Initiation: stock CM1 `iinit = 3` three-warm-bubble line trigger.
- Lower boundary: surface heat/moisture fluxes disabled.
- Domain: 120 km x 120 km.
- Grid: 120 x 120 x 40; 1 km dx/dy; 500 m dz.
- Model top: 20 km.
- Rayleigh damping start: 15 km.
- Duration: 7200 s.
- Output cadence: 900 s.
- Time step: 6 s.

Runtime and integrity:

- Completed normally with exit code 0.
- Queue interval was about 12 minutes wall-clock.
- CM1 reported total runtime 666.125 s.
- Ingest completed and retained the run for Explore.
- Runtime warning: `IEEE_UNDERFLOW_FLAG` only.
- Output: 10 NetCDF paths cataloged, including 9 model-output frames plus stats.

Actual cloud outcome:

- Category: weak shallow cloud / failed deep-tower candidate.
- First cloud: 1800 s.
- Coherent cloud-object top: 1250 m.
- Hydrometeor envelope top: 1250 m.
- Highest liquid cloud top: 1250 m.
- Maximum updraft: 0.890 m/s at 2700 s.
- Maximum cloud water: 8.878e-4 kg/kg at 4500 s.
- Rain water aloft: trace, first detected at 2700 s; max qr 7.22e-6 kg/kg.
- Surface rain: trace, max 2.82e-6 cm.
- Reflectivity: available but not meaningful; max diagnostic value 0.0 dBZ
  with negative values during the shallow-cloud period.

Ratings:

- Visual-interest rating: 2/5.
- Worth-the-compute rating: 4/5 for calibration, 1/5 for visual output.

## Recommendation

For the next calibration step, spend the next real scout only on a supported
`deep_tower_opportunity` candidate above the weak band, preferably one with
effective CAPE at least 1500 J/kg and richer 0-3 km moisture, so the analyzer
gets a positive-or-near-positive test instead of another weak shallow-cloud
case.
