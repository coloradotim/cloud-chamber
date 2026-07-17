# Cloud Chase 004: Slidell Trigger Suitability

Issue context: follow-up to the supported Slidell Deep-Tower miss.

## Question

Why did the same `deep_tower_benchmark_v0` recipe produce a major Fort Worth
tower but no meaningful Slidell convection, even though both were supported
Deep-Tower opportunities?

## Fort Worth Summary

Fort Worth `USM00072249`, valid `1997-05-27T00:00:00Z`, used the Deep-Tower
Benchmark: stock CM1 `iinit = 3`, disabled surface fluxes, 120 km domain, 2 h,
15 min output, 20 km model top. It produced first deep convection by 1800 s,
coherent cloud top near 17.25 km, hydrometeor envelope near 19.75 km, maximum
updraft 54.13 m/s, surface rain, and 65.38 dBZ reflectivity.

## Slidell Summary

Slidell `USM00072233`, valid `1998-06-20T00:00:00Z`, scored 84.4 supported
Deep-Tower opportunity. The same benchmark completed normally but produced no
coherent cloud, no precipitation, maximum updraft about 0.79 m/s, and only a
tiny raw hydrometeor trace to about 2.75 km.

The candidate evidence explains why it looked tempting: surface-based CAPE was
3762 J/kg, estimated LCL was 275 m, mean qv was 21.5 g/kg in 0-500 m and
19.6 g/kg in 0-1 km. The same evidence also carried a
`near_surface_discontinuity_caveat`: the lowest copied level had 31.0 g/kg qv,
but qv fell to 20.5 g/kg by 116 m and 16.9 g/kg by 500 m.

## Physical Comparison At The Warm-Bubble Layer

The stock `iinit = 3` trigger is not a surface parcel. In the first model output
for both runs, the thermal appeared as expected: a maximum potential-temperature
anomaly of about 1.92 K near 1.25 km, with meaningful warming through roughly
0.75-2.25 km and only weak warming near 0.25 km.

| Normalized input near 1.4 km | Fort Worth | Slidell |
| --- | ---: | ---: |
| theta | 309.52 K | 307.01 K |
| temperature | 21.17 C | 21.38 C |
| qv | 14.21 g/kg | 12.28 g/kg |
| RH | 74.2% | 65.9% |
| saturation deficit | 5.01 g/kg | 6.58 g/kg |
| pressure | 838.6 hPa | 864.9 hPa |
| density | 0.984 kg/m3 | 1.015 kg/m3 |

Layer context matters more than the point value. From 500-1400 m, Fort Worth
averaged about 17.9 g/kg qv and 81% RH, while Slidell averaged about
14.5 g/kg qv and 66% RH. Slidell's richest inflow evidence was packed into a
very shallow near-surface layer that the fixed warm-bubble core did not strongly
lift. A +2 K parcel started at the Slidell bubble core had an estimated LCL near
2.48 km, above most of the imposed thermal depth; the Fort Worth bubble-core
parcel was closer to saturation and recovered stronger buoyancy aloft.

## Trigger Verification

The failed Slidell benchmark was not missing the trigger. The namelist used
`iinit = 3`, and the first output frame contained the same lower-tropospheric
thermal structure as Fort Worth.

To test whether fixed warm-bubble placement alone was the limiting factor, a
single additional rung was added and run:
`deep_tower_low_level_lift_v0`, stock CM1 `iinit = 9`, `Dmax = -1.0e-3 s^-1`,
0-2 km forced-convergence depth, 10 km horizontal scale, 900 s duration, same
120 km / 2 h / disabled-flux scout shape. The forcing appeared by 900 s, with
near-surface convergence about 1.46e-3 s^-1 and maximum vertical velocity about
0.74 m/s in that frame.

That follow-up completed and auto-ingested as
`cloud_chase_004-slidell_low_level_lift_probe`: normal termination, underflow
warning only, nine output frames through 7200 s. Outcome: no cloud, no raw
hydrometeor trace, no rain, max updraft 1.28 m/s at 900 s, max qc 0, max qr 0,
max reflectivity 0.

## Conclusion

Fort Worth and Slidell responded differently for physically understandable
reasons: Fort Worth's bubble-layer thermodynamic profile could sustain the
imposed thermal into deep buoyant growth, while Slidell's apparent opportunity
was dominated by a shallow, discontinuous near-surface moisture/CAPE signal that
did not translate into cloud under either the fixed warm bubble or one low-level
forced-convergence rung.

Choose outcome **B: the analyzer overestimates atmospheric potential** for this
specific profile. The fixed trigger was a plausible suspect, but the low-level
lift rung made the same no-cloud result, so trigger placement alone is not the
best product explanation.

## Recommendation

Record Slidell `USM00072233` at `1998-06-20T00:00:00Z` as a negative supported
Deep-Tower trial for both `deep_tower_benchmark_v0` and
`deep_tower_low_level_lift_v0`, and use it in the next analyzer review to
handle near-surface discontinuity / surface-CAPE-dominated profiles without
retuning the opportunity weights in this change.
