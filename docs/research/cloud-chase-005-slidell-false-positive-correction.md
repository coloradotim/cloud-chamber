# Cloud Chase 005: Slidell False-Positive Correction

## Scope

This note records the bounded analyzer correction after the Slidell supported
Deep-Tower miss, plus the single Topeka period-of-record Deep-Tower Benchmark
trial used to test the corrected selector. It does not add a candidate-supply
path, scoring platform, diagnostics framework, or new CM1 recipe.

## Correction

The `deep_tower_opportunity` selector now treats a large near-surface
temperature or moisture discontinuity as a hard caveat for the Deep-Tower
Benchmark. A discontinuous profile cannot return `supported`, and surface-based
CAPE from the suspect lowest copied level no longer dominates the
recipe-specific recommendation. In that case the selector uses mixed-layer CAPE
for the CAPE gate and records a caveat that surface-based CAPE was ignored.

The selector also adds one trigger-layer moisture check:
`trigger_layer_mean_qv_750_2250m_g_kg`. This is the mean qv through the
approximate stock `iinit = 3` warm-bubble layer. It is evidence about what the
fixed benchmark trigger is actually lifting, not a new trigger recipe or a new
diagnostics framework.

## Calibration Checks

- Fort Worth-like clean profile remains supported:
  `USM00072249`, `1997-05-27T00:00:00Z`, revised score 81.7.
- Slidell-like profile with high surface CAPE and a near-surface discontinuity
  is capped below supported:
  `USM00072233`, `1998-06-20T00:00:00Z`, revised score 65.0 weak.
- North Platte-like profile falls to unavailable because the trigger-layer qv is
  poor for the fixed warm-bubble layer:
  `USM00072562`, `2026-07-02T00:00:00Z`, revised score 44.0.

## Candidate Supply Finding and Run Selection

Re-ranking the current recent-cache analyzer pool found no package-ready
candidate meeting the requested run predicate:

- supported revised opportunity;
- no near-surface discontinuity;
- strong mixed-layer CAPE;
- adequate trigger-layer and lower-3-km moisture.

That is not evidence that summer Midwest severe environments are absent. It is
evidence that the current recent-cache analyzer pool is too narrow for this
selection task.

A bounded direct scan of existing local period-of-record cached station files
did find clean supported candidates. The run target selected by PM decision was:

- Topeka `USM00072456`, valid `2017-06-18T00:00:00Z`;
- station metadata: `TOPEKA/MUN.; KS.`, 39.0722 N, 95.6305 W,
  elevation 268.1 m MSL;
- source file: `USM00072456-data.txt`;
- source-file SHA-256:
  `de1817eaec60d6d47ad5840d0a3e8998dbadf943d026edf74a3950bfdcf3aad2`;
- selection provenance: `direct_local_period_of_record_scan`;
- caveat:
  `current_product_analyzer_does_not_yet_search_local_period_of_record_collection`;
- revised opportunity 78.0 supported;
- surface-based CAPE 1722.0 J/kg;
- mixed-layer CAPE 1787.5 J/kg;
- trigger-layer qv 17.031 g/kg;
- mean qv 0-3 km 15.298 g/kg;
- no near-surface discontinuity;
- normalized observed sounding: 12 rendered levels, lowest level 0.0 m AGL,
  top 18461.9 m AGL, complete thermodynamic and observed wind profile;
- package readiness: usable, with `needs_review` source/provenance caveats
  about preserved IGRA flags, station-elevation join, surface anchoring, and
  upper-profile truncation.

The current product analyzer UI did not discover this candidate. It came from
the direct local period-of-record scan.

## Topeka CM1 Scout

- run id: `cloud_chase_005-topeka_20170618_deep_tower_scout`;
- result id: `result-cloud_chase_005-topeka_20170618_deep_tower_scout`;
- recipe: `deep_tower_benchmark_v0`;
- initiation: stock CM1 `iinit = 3`;
- run shape: 120 km domain, `120 x 120 x 40`, 20 km model top, 2-hour
  duration, 15-minute output cadence, 6-second timestep, surface fluxes
  disabled, existing full output set.

Runtime integrity: completed and ingested with 9 model output frames, exit code
0, normal CM1 termination reported, and an `IEEE_UNDERFLOW_FLAG` runtime caveat
only.

Outcome:

- actual cloud category: transient shallow cloud;
- first cloud time: 900 s;
- first deep-convection time: none;
- coherent cloud top: 1750.0 m;
- liquid cloud top: 1750.0 m;
- hydrometeor-envelope top: 1750.0 m;
- maximum updraft: 0.554 m/s at 900 s;
- maximum cloud water: `7.185e-05 kg/kg`;
- rain water aloft: no meaningful rain water, maximum `5.368e-10 kg/kg`;
- surface rain: 0.0 cm;
- maximum reflectivity: 0.0 dBZ metadata maximum; no reflective precipitation
  signal after model start;
- visual-interest rating: 1/5;
- worth-the-compute rating: 1/5.

The corrected selector did not earn confidence on this run: a second supported
candidate outside the recent-cache pool still produced only a weak shallow
response under the fixed Deep-Tower Benchmark trigger.

## Recommendation

Stop and request PM review before retuning the score, running another candidate,
or changing the candidate-supply path.
