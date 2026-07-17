# Cloud Chase 005: Deep-Tower Benchmark Audit

## Observed evidence

PR #355 no longer treats the Slidell/Topeka work as a validated scoring
correction. The durable product change is narrower: a major near-surface
discontinuity prevents a clean `supported` Deep-Tower recommendation, and the
score uses mixed-layer CAPE instead of allowing one suspect lowest level to
dominate. The retained trigger-layer qv field is descriptive evidence only: it
is an unweighted mean of available rendered sounding levels from 750-2250 m
AGL, not a thickness-weighted layer mean and not a validated recommendation
gate.

The exact CM1 benchmark artifacts show that the Fort Worth success, Slidell
miss, and Topeka 2017 miss used the same Deep-Tower Benchmark namelist:
`3417c51c22a92c09e57298389fda5130b2267cc7f605c026ac950042aa7d5cee`.
They also used the same `cm1_config.txt` hash,
`2cdf5ef37465a5b55b07eca57c710e004656d5643d6e2d2f507d4448bcb692d3`.
The benchmark configuration was `iinit = 3`, `120 x 120 x 40`, 1 km
horizontal spacing, 500 m vertical spacing, 20 km model top, 7200 s duration,
900 s output cadence, 6 s timestep, Rayleigh damping enabled from 15 km, and
surface fluxes disabled. Runtime integrity was caveated only by
`IEEE_UNDERFLOW_FLAG` for the three main runs.

| Case | Run id | Sounding | App commit | `input_sounding` SHA-256 | Outcome |
|---|---|---|---|---|---|
| Fort Worth 1997 | `cloud_chase_001-fort_worth_deep_tower_probe` | `USM00072249`, `1997-05-27T00:00:00Z` | not recorded | `08a9012ff831568cf6af45713d217a6c448067a85a459e830f40aed00d6826a5` | coherent cloud top 17.25 km, hydrometeor envelope 19.75 km, max updraft 54.13 m/s, surface rain 0.721 cm |
| Slidell 1998 | `dry-run-2b944f5bc653` | `USM00072233`, `1998-06-20T00:00:00Z` | not recorded | `7fbba5362d048dbfa7f1a69c101c0321c33a377132cf5bc2f601acde95dabd03` | no coherent cloud, liquid top 2.75 km, max updraft 0.79 m/s, no surface rain |
| Topeka 2017 | `cloud_chase_005-topeka_20170618_deep_tower_scout` | `USM00072456`, `2017-06-18T00:00:00Z` | `597e8fd5cd8b0c6e07ca23ac071e07fda522abae` | `38304066848f39f66e265872456d5f3f39bf7f2db3078b42b0bbd51b1564b392` | transient shallow cloud, coherent top 1.75 km, max updraft 0.55 m/s, no surface rain |
| North Platte 2026 | `cloud_chase_001-north_platte_high_potential` | `USM00072562`, `2026-07-02T00:00:00Z` | not recorded | `437b0ec1791021a41d86aee8e547dbb38892e484395c28922695cc852ada13af` | exact outputs available; result metadata absent |
| Topeka 2026 | `cloud_chase_003-topeka_deep_tower_opportunity` | `USM00072456`, `2026-06-10T00:00:00Z` | not recorded | `f8b8e8eb556403761fed2980c1490046ba3c30e206e5aee1bb0fda7378ac270a` | coherent cloud top 1.25 km, max updraft 0.89 m/s |

The CM1 executable was `/Users/timpeterson/cm1r21.1/run/cm1.exe`, SHA-256
`5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1`.
The source tree is not a git checkout. A text-source hash over the local CM1
source tree was
`87cb9ea94b623d4c9e026424b5e2967bf829c17e7e8621a1360423b41373c2fa`;
`/Users/timpeterson/cm1r21.1/src/init3d.F` was
`9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28`.

The authoritative `init3d.F` implementation defines `iinit = 3` as a line of
three warm bubbles. The source constants are: `nbub = 3`, `ric = 30000 m`,
`rjc = 3000, 33000, 63000 m`, `zc = 1400 m`, `bhrad = 10000 m`,
`bvrad = 1400 m`, and `bptpert = 2.0 K`. The perturbation is a
cosine-squared potential-temperature perturbation. `maintain_rh = .false.`, so
the warm bubble does not modify qv. These center/radius/temperature constants
are defined by CM1 source, not by Cloud Chamber package controls.

The first output frame confirms that the three main runs received materially
the same initial trigger. At `t = 0`, each had `theta_p_max = 1.9198 K` at
approximately x = 29.5 km, y = 2.5 km, z = 1.25 km, with `theta_p > 0.1 K`
from x = 22.5-37.5 km, y = -4.5-59.5 km, z = 0.25-2.25 km, and zero maximum
vertical velocity. The third source bubble center is partly outside the
120 km domain in all three cases because CM1 places it at y = 63 km while the
resolved scalar grid reaches about y = 59.5 km.

The early response diverged after the common trigger. At 900 s, Fort Worth had
maximum vertical velocity 4.23 m/s near z = 2.0 km; Slidell had 0.79 m/s near
z = 1.0 km; Topeka 2017 had 0.55 m/s near z = 1.0 km. At 1800 s, Fort Worth
had maximum vertical velocity 54.13 m/s near z = 12.5 km; Slidell remained
0.45 m/s and Topeka 2017 remained 0.53 m/s.

Rendered lower-profile evidence from the exact normalized soundings supplied
to CM1:

| Case | levels / below 3 km / top | Bubble center estimate at 1.4 km | Trigger qv evidence |
|---|---|---|---|
| Fort Worth | 50 / 10 / 19.31 km | 838.6 hPa, 21.2 C, theta 309.52 K, qv 14.21 g/kg, saturation deficit 4.67 g/kg | 6 available levels, unweighted mean 13.34 g/kg |
| Slidell | 84 / 15 / 19.77 km | 864.9 hPa, 21.4 C, theta 307.01 K, qv 12.28 g/kg, saturation deficit 6.25 g/kg | 9 available levels, unweighted mean 12.42 g/kg |
| Topeka 2017 | 12 / 4 / 18.46 km | 829.9 hPa, 20.4 C, theta 309.79 K, qv 15.43 g/kg, saturation deficit 2.73 g/kg | 1 available level, unweighted mean 17.03 g/kg |

| Case | z m | dz m | p hPa | T C | theta K | qv g/kg | RH % | sat deficit g/kg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fort Worth | 2.8 |  | 981.6 | 32.1 | 306.87 | 22.19 | 71.8 | 8.71 |
| Fort Worth | 33.8 | 31 | 978.2 | 31.8 | 306.87 | 22.00 | 72.2 | 8.48 |
| Fort Worth | 535.8 | 502 | 925.0 | 27.8 | 307.72 | 18.76 | 73.5 | 6.76 |
| Fort Worth | 860.8 | 325 | 891.8 | 24.8 | 307.85 | 20.22 | 91.4 | 1.90 |
| Fort Worth | 887.8 | 27 | 889.0 | 24.7 | 308.02 | 18.82 | 85.3 | 3.24 |
| Fort Worth | 1281.8 | 394 | 850.0 | 21.8 | 308.95 | 15.77 | 81.6 | 3.56 |
| Fort Worth | 1614.8 | 333 | 818.0 | 20.1 | 310.55 | 11.36 | 62.9 | 6.71 |
| Fort Worth | 1893.8 | 279 | 791.9 | 18.2 | 311.41 | 9.53 | 57.5 | 7.04 |
| Fort Worth | 2240.8 | 347 | 760.4 | 17.1 | 313.85 | 4.32 | 26.8 | 11.78 |
| Fort Worth | 2938.8 | 698 | 700.0 | 11.9 | 315.59 | 3.26 | 26.2 | 9.20 |
| Slidell | 0.1 |  | 1012.8 | 34.4 | 306.44 | 31.03 | 90.9 | 3.11 |
| Slidell | 116.1 | 116 | 1000.0 | 32.5 | 305.65 | 20.47 | 66.0 | 10.56 |
| Slidell | 152.1 | 36 | 996.0 | 31.8 | 305.30 | 17.38 | 58.1 | 12.54 |
| Slidell | 414.1 | 262 | 967.4 | 29.1 | 305.12 | 17.14 | 65.1 | 9.19 |
| Slidell | 812.1 | 398 | 925.0 | 25.5 | 305.37 | 15.82 | 71.1 | 6.42 |
| Slidell | 939.1 | 127 | 911.7 | 24.1 | 305.20 | 15.65 | 75.5 | 5.09 |
| Slidell | 1081.1 | 142 | 897.1 | 24.0 | 306.50 | 12.94 | 61.8 | 8.01 |
| Slidell | 1358.1 | 277 | 869.1 | 21.8 | 307.00 | 11.49 | 60.8 | 7.41 |
| Slidell | 1442.1 | 84 | 860.7 | 21.0 | 307.02 | 13.07 | 71.9 | 5.10 |
| Slidell | 1550.1 | 108 | 850.0 | 20.3 | 307.38 | 11.07 | 62.9 | 6.53 |
| Slidell | 1744.1 | 194 | 831.1 | 18.8 | 307.78 | 11.64 | 71.0 | 4.76 |
| Slidell | 1862.1 | 118 | 819.8 | 18.3 | 308.46 | 9.58 | 59.5 | 6.52 |
| Slidell | 2083.1 | 221 | 798.9 | 16.7 | 309.03 | 10.52 | 70.5 | 4.40 |
| Slidell | 2442.1 | 359 | 765.8 | 13.8 | 309.66 | 9.14 | 70.8 | 3.77 |
| Slidell | 2902.1 | 460 | 725.0 | 10.6 | 311.03 | 7.79 | 70.6 | 3.24 |
| Topeka 2017 | 0.0 |  | 971.0 | 32.2 | 307.93 | 21.23 | 67.6 | 10.19 |
| Topeka 2017 | 432.9 | 433 | 925.0 | 27.6 | 307.52 | 17.84 | 70.7 | 7.38 |
| Topeka 2017 | 1176.9 | 744 | 850.0 | 21.4 | 308.53 | 17.03 | 90.3 | 1.82 |
| Topeka 2017 | 2843.9 | 1667 | 700.0 | 14.0 | 317.92 | 5.09 | 35.6 | 9.23 |

The Topeka 2017 selection came from a direct local period-of-record scan, not
from the current analyzer UI. Its recorded selection provenance is
`direct_local_period_of_record_scan`; source collection is
`local_igra_period_of_record_cache`; source file is `USM00072456-data.txt`;
source-file hash is
`de1817eaec60d6d47ad5840d0a3e8998dbadf943d026edf74a3950bfdcf3aad2`.
The current product analyzer does not yet search that local period-of-record
collection.

The current simple parcel diagnostics are screening estimates. The surface
parcel starts from the lowest finite rendered level. The mixed-layer parcel is
an arithmetic mean of rendered levels from 0-500 m and requires at least two
levels. LCL uses `125 * (T - Td)` meters. The lifted parcel samples the
rendered sounding grid plus the LCL, follows dry ascent below LCL and an
approximate moist lapse-rate integration above LCL, and integrates CAPE over
all positive layer-mean buoyancy. CIN is accumulated only before the first
positive layer. LFC is the first positive-buoyancy crossing; EL is the first
negative crossing after LFC. Because CAPE can continue accumulating after the
first reported EL, Fort Worth can show large simple CAPE while reporting a
surface-based EL near 98 m. No trusted independent parcel library was installed
locally (`metpy` and `sharppy` were not available), so no external parcel
cross-check was performed.

Current branch diagnostics from the rendered profiles are:

| Case | SBCAPE | MLCAPE | SBCIN | MLCIN | LFC | EL | mean qv 0-3 km | trigger qv evidence | moisture depth |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fort Worth | 1781.0 | 1820.3 | 0.0 | -5.3 | 2.8 m | 98.2 m | 14.62 g/kg | 13.34 g/kg | 1893.8 m |
| Slidell | 3762.4 | 1256.2 | 0.0 | -4.4 | 0.1 m | unavailable | 14.32 g/kg | 12.42 g/kg | 2902.1 m |
| Topeka 2017 | 1722.0 | 1787.5 | 0.0 | -0.2 | 0.0 m | 12548.9 m | 15.30 g/kg | 17.03 g/kg | 1176.9 m |

## Reasonable inferences

The three main atmospheres received the same stock `iinit = 3` thermal at model
start. The Fort Worth success versus Slidell and Topeka misses is therefore
not explained by a different Cloud Chamber recipe, a different namelist, or a
missing initial warm bubble.

The Slidell guardrail is still justified as a data-quality/product-semantics
change. Its rendered profile has an extreme lowest-level qv value followed by a
sharp low-level moisture drop, and the surface-based CAPE is much larger than
mixed-layer CAPE. That is enough to prevent a clean `supported`
recommendation, but it does not prove Slidell could never support deep
convection under a different trigger or configuration.

Topeka 2017 is the more important miss for product confidence. It was clean
with respect to the near-surface discontinuity rule and still scored about
78 supported, yet produced only a transient 1.75 km cloud. Its rendered profile
is sparse below 3 km, and the very favorable trigger-layer qv evidence comes
from one available level. The actual profile also dries sharply by 2.84 km.
Those facts make the analyzer evidence weaker than the headline score, but they
do not by themselves establish a validated physical separator.

The current parcel diagnostics do not represent the actual `iinit = 3` bubble
parcel. They answer a simpler surface or mixed-layer lifted-parcel question on
the rendered sounding grid. They can be useful evidence, but the Fort Worth,
Slidell, and Topeka outcomes show that they are not a reliable standalone
recommender for this fixed benchmark trigger.

## Untested hypotheses

The stock 2 K, 1.4 km-center warm bubbles may be too weak, too high, or too
geometrically specific for many otherwise interesting observed soundings.

Topeka 2017 may have failed because sparse lower-tropospheric sampling hid a
layer structure that mattered to the fixed bubble response.

Slidell may have failed because the lowest-level moisture/CAPE signal was not
representative of the effective inflow actually lifted by the CM1 thermal.

Fort Worth may have had a favorable combination of local moisture, lapse rate,
and vertical structure near the bubble that the current scalar diagnostics do
not isolate.

## Decision

### C. No clear separator exists

The fixed stock `iinit = 3` Deep-Tower Benchmark is not predictably related to
the current sounding diagnostics. The available artifacts show benchmark
consistency and real outcome separation, but they do not reveal a validated
profile or trigger-fit criterion that cleanly separates Fort Worth from both
Slidell and Topeka 2017.

Recommendation: stop presenting `deep_tower_opportunity` as a reliable
recommender for this fixed recipe. Keep Fort Worth as a known-good
demonstration, keep the narrow near-surface guardrail, and reserve any future
work for PM review of an adaptive, explicitly parameterized thermal setup.
