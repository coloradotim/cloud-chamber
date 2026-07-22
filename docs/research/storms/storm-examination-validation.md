# Storm Examination Validation

## 1. Status and decision question

**Status:** Gate C examination completed against one accepted retained run. **Disposition:** `advance_to_storms_world_definition`.

Decision question:

> Can the accepted benchmark be examined through a bounded Cloud Chamber-native experience that reveals important storm structures and relationships honestly, clearly, and beautifully enough to justify defining a third Cloud World?

Yes. The coordinated plan and vertical-section experience exposes three distinct, coherent relationships: organized rising motion with rotation, the vertical and horizontal partitioning of condensate and precipitation, and the meeting of low-level ascent, descent, rain, and model-relative flow. This is Gate C evidence, not approval of a World identity or production implementation.

Evidence labels used below:

- **Native evidence:** a retained CM1 variable shown without scientific transformation beyond unit conversion.
- **Derived evidence:** an explicitly formula-defined combination or reduction of native variables.
- **Directly visible:** a relationship present in one displayed retained history.
- **Bounded inference:** an interpretation supported by ordered retained checkpoints but not continuously observed.
- **Product hypothesis:** a proposed way to help a user reason about the Simulation.
- **Unresolved:** a question the retained evidence does not answer.
- **PM decision required:** a product choice reserved for Gate D or later approval.

## 2. Accepted identity and retained run

- Run ID: `quarter-circle-supercell-official-20260722T142521Z`
- Case ID: `cm1_r21_1_quarter_circle_supercell_official_v0`
- CM1 release: `21.1`
- Official commit: `0f734f64efa89a684963a66d2ac32db67617912b`
- Gate A artifact: `docs/research/storms/canonical-deep-convection-benchmark-mapping.md`
- Gate B artifact: `docs/research/storms/canonical-deep-convection-run-report.md`

The examination reads the nine preserved `cm1out_*.nc` histories at 0 through 120 minutes. No CM1 process was started, no history was modified, and the Fort Worth run was not used.

## 3. Examination implementation and non-product boundary

The bounded path is an unlinked local route at `/research/storm-examination`. A dedicated reader verifies the exact completed run and case, caches the retained inventory by artifact fingerprint, opens only the selected history, and returns one cropped native-grid plan view plus coordinated x-z and y-z sections. It never sends a full 3-D volume to the browser. Stable scales remain fixed across all retained times.

The surface reuses Cloud Chamber's Integrated Explore workspace, compact Lens selection, attached controls, vertical legend, timeline, selected-point Context inspector, and maximize/restore behavior. It is marked `Gate C research surface`. It does not create a World route, navigation entry, final Lens contract, Recipe, Lab variation, storm registry, or general storm framework.

## 4. Source fields and derived diagnostics

All 3-D fields below have native dimensions `time x zh x yh x xh` = `1 x 40 x 120 x 120` and are scalar-grid products. The grid is 1 km in x/y and 0.5 km in z. `uh` and `rain` have `time x yh x xh` = `1 x 120 x 120`. Native u/v/w staggered fields exist, but the examination uses the emitted scalar-grid interpolated products where coordination requires collocation.

| Concept | Evidence and units | Direct display | Inference and limit | Gate C use |
|---|---|---|---|---|
| Vertical motion | Native `winterp`, m/s | Signed fixed-scale plan fields and sections | Rising/descending at a cell; not a trajectory | First experience |
| Rotation | Native `zvort`, s^-1; native `uh`, m^2/s^2 | Cyclonic 3.25 km vorticity and 2-5 km AGL UH outlines | Colocation supports organized rotating-updraft interpretation; not tornado diagnosis | First experience |
| Reflectivity | Native `dbz`, dBZ | Level sections and derived column maximum | Echo organization, not observational equivalence | First experience |
| Surface rain | Native `rain`, cm | Derived mm footprint | Accumulation at retained time; not instantaneous rate | First experience |
| Hydrometeors | Native `qc`, `qr`, `qi`, `qs`, `qg`, kg/kg | Species categories and inspector values in g/kg | Mass partition, not literal particle appearance; `qg` is hail-treated large ice, not proof of hail at ground | First experience |
| Horizontal flow | Native `uinterp`, `vinterp`, m/s | Thinned arrows at the lowest scalar level | Model-relative flow only; ground-relative flow adds `(12.5, 3.0)` m/s | First experience |
| Surface pressure/wind swaths | Native `sps`, `sws` and translated products exist | Not displayed | Could support later outflow research, but does not establish thermodynamic cold-pool structure | Later research |
| Number concentration | Native `nci`, `ncs`, `ncr`, `ncg`, #/kg | Not displayed | Adds microphysical complexity without a clear first-use question | Rejected for first version |
| Temperature/buoyancy | No retained direct near-surface perturbation or buoyancy field in the required payload | Not displayed | Cold-pool diagnosis is unsupported | Rejected for this run |

Formula-documented derived evidence:

- Total condensate: `1000 * (qc + qr + qi + qs + qg)`, in g/kg.
- Column-maximum total condensate: `1000 * max_z(qc + qr + qi + qs + qg)`.
- Dominant hydrometeor: largest native species mass at the level of column-maximum total condensate, shown only where total condensate is at least 0.05 g/kg.
- Precipitating condensate: `1000 * (qr + qs + qg)`, in g/kg.
- Composite reflectivity: `max_z(dbz)`, in dBZ.
- Accumulated rain depth: `10 * rain`, converting native cm to display mm.
- Primary updraft: full-volume `argmax(winterp)` for the selected history.
- Storm region: a native-grid crop extending at most 30 km from the primary updraft in x and y; no interpolation.
- Selected-point distance: horizontal Euclidean distance from the selected cell to the primary-updraft x/y position.

## 5. Mature evolution, 45-120 minutes

Fixed scales make the following changes comparable rather than frame-rescaled:

| Time | Primary w (m/s) | Primary x/y/z (km) | 3.25 km w min/max (m/s) | 1.25 km w min/max (m/s) | Condensate max (g/kg) | Rain max (mm) |
|---:|---:|---|---|---|---:|---:|
| 45 min | 49.0 | -7.5 / 5.5 / 10.25 | -3.59 / 18.36 | -5.56 / 5.56 | 12.99 | 15.03 |
| 60 min | 55.1 | -8.5 / 5.5 / 11.25 | -7.36 / 20.68 | -6.67 / 8.55 | 14.74 | 37.86 |
| 75 min | 60.1 | -7.5 / 2.5 / 10.25 | -10.72 / 23.53 | -8.08 / 10.72 | 15.20 | 65.46 |
| 90 min | 58.7 | -6.5 / -1.5 / 10.25 | -8.13 / 22.82 | -9.14 / 9.48 | 14.51 | 76.44 |
| 105 min | 59.2 | -4.5 / -5.5 / 9.25 | -9.88 / 25.79 | -7.60 / 12.52 | 14.97 | 78.45 |
| 120 min | 55.7 | -1.5 / -11.5 / 9.25 | -8.83 / 25.44 | -7.33 / 12.39 | 15.51 | 80.91 |

**Directly visible:** the 45-minute storm is already deep, precipitating, and organized. The primary updraft remains strong through 120 minutes; the plan view keeps cyclonic rotation and UH near the main rising-motion core. Sections show the main updraft embedded in deep condensate and reflectivity. The precipitation footprint expands substantially, and later frames contain broader cloud structure plus additional convective and rotating features.

**Bounded inference:** the ordered primary-updraft positions support a persistent storm track in the translating frame. They do not establish continuous object identity between 15-minute histories. Secondary structures after 60 minutes establish cell multiplicity but not split parentage. Upper-level condensate and motion overlap the 15-20 km Rayleigh layer; the display cannot diagnose the layer's causal effect.

## 6. Candidate user questions

Accepted questions:

- Where is the strongest updraft, and where is cyclonic rotation relative to it?
- How do the updraft, reflectivity envelope, and precipitation structure align in plan and section?
- How are cloud liquid, rain, cloud ice, snow, and hail-treated large ice partitioned?
- Where do low-level ascent, descent, accumulated rain, and horizontal flow meet?
- How do the storm and its precipitation footprint broaden across retained checkpoints?
- Which upper structures reach the damping-layer region?

Rejected or qualified questions:

- Why did a secondary cell form or split? Parentage and causal process are unresolved at 15-minute cadence.
- Where is the cold pool? Thermodynamic evidence is insufficient.
- Is there a tornado or damaging hail? The model fields do not authorize hazard diagnosis.
- What happened at an exact initiation, occlusion, or decay time? The retained cadence is too coarse.
- Does the run reproduce a real observed storm? It is an idealized benchmark, not an observational match.

## 7. Candidate Lens analysis

### Rotating Updraft

- **Product hypothesis:** answer, "Where is the storm rising and rotating as one organized structure?"
- **Fields:** native `winterp` at 3.25 km, `zvort` at 3.25 km, `uh`, and `dbz`; derived composite reflectivity.
- **Encoding:** Trade Cumulus signed w palette is primary; purple cyclonic-vorticity, black UH, brown reflectivity, and optional condensate outlines remain subordinate.
- **Coordination:** plan view plus x-z/y-z sections through the selected point or strongest updraft.
- **Inspector:** w, vorticity, UH, reflectivity, location, time, distance, native/derived status.
- **Hidden by default:** anticyclonic-vorticity interpretation, species detail, model-relative winds, and every available CM1 variable.
- **Distinct value:** establishes spatial organization of rise and rotation, not merely storm intensity.
- **Risks:** thresholds can imply object boundaries; UH and vorticity colocation must not become tornado or mesocyclone certification.

### Cloud and Precipitation

- **Product hypothesis:** answer, "How are liquid, ice, and precipitation arranged through the storm?"
- **Fields:** native `qc`, `qr`, `qi`, `qs`, `qg`, `dbz`, and `winterp`; derived total condensate, dominant category, composite reflectivity, and w contours.
- **Encoding:** category hue communicates species; mass-driven opacity communicates total condensate; black reflectivity and red/blue w contours provide structure without a competing heatmap.
- **Coordination:** column category in plan and native-grid species sections through the selected point.
- **Inspector:** each native species in g/kg, derived total condensate, reflectivity, location, time, and evidence status.
- **Hidden by default:** number concentrations and literal particle imagery.
- **Distinct value:** turns the storm from one opaque cloud mass into inspectable liquid, frozen, and precipitating structure.
- **Risks:** dominant-category color hides mixtures; hail-treated `qg` can be misread as observed hail; large-ice dominance can visually overwhelm weaker categories.

### Low-Level Interactions

- **Product hypothesis:** answer, "How do low-level ascent, descent, rain, and horizontal flow meet beneath the storm?"
- **Fields:** native `winterp` at 1.25 km, `uinterp`, `vinterp`, `dbz`, `rain`, and precipitating hydrometeors; derived rain in mm, composite reflectivity, and precipitating condensate.
- **Encoding:** signed low-level w remains primary; native model-relative arrows, a 2 mm rain-footprint outline, reflectivity outline, and optional precipitating-condensate sections remain separable.
- **Coordination:** plan interaction map plus full-depth x-z/y-z motion and precipitation context.
- **Inspector:** w, rain, rain water, reflectivity, model-relative u/v, location, time, and evidence status.
- **Hidden by default:** unsupported cold-pool label, ground-relative conversion, pressure swaths, and thermodynamic claims.
- **Distinct value:** exposes the near-surface relationship the user asked to investigate without conflating it with rotation or microphysical partition.
- **Risks:** rain accumulation is path history rather than instantaneous process; model-relative flow can be misread; no temperature/buoyancy evidence establishes outflow thermodynamics.

## 8. Viewpoints and coordination

- **Storm region:** the useful default. A 60 x 60 km native crop preserves the primary structure and nearby secondary cells while keeping one-kilometer cells legible.
- **Full domain:** necessary for boundary separation, translating-frame context, and checking whether focus hides other convection. It is less useful for detailed examination.
- **Horizontal plan:** essential for rotation, rain footprint, track context, and cell multiplicity.
- **x-z and y-z sections:** both are necessary because storm tilt and secondary structure differ by direction. Clicking any view coordinates both sections and the plan marker by original native-grid indices.
- **3-D:** rejected for Gate C. The plan/section combination reveals the evaluated relationships with less occlusion and more exact coordinates. This does not prohibit later 3-D research.
- **Maximize/restore:** useful for close examination and verified to expand the coordinated views rather than merely hide chrome.

## 9. Timeline semantics

The reader validates all nine retained histories. The examination timeline intentionally exposes only the six mature histories at 45, 60, 75, 90, 105, and 120 minutes. Previous, next, play/pause, slider, and playback speed operate within those six checkpoints using the shared Explore grammar. Scales remain fixed during playback.

Phase labels describe what is visible at a checkpoint. They are not exact event markers. The 15-minute cadence does not support exact initiation, splitting, occlusion, or decay times, and continuity between frames remains a bounded inference.

## 10. Inspector semantics

The Context inspector supplies Lens question, concise state labels, x/y/z, model time, value and unit, native/derived status, coordinate-frame meaning, distance to the selected primary feature, and the most relevant scientific caveat. It avoids a variable dump. Selected cells coordinate all views; a button returns sections to the strongest updraft. Context collapses to prioritize the scientific views and restores without losing state.

`Rising`, `Descending`, `Near neutral`, `Condensate present`, and `Rain footprint` are thresholded descriptions of current values. They are not process histories. The inspector explicitly identifies winds as model-relative and `qg` as hail-treated large ice.

## 11. Visual review findings

Desktop review used Playwright against the retained backend in a 1920 x 1080 browser viewport. Eighteen Lens-by-checkpoint screenshots cover every candidate Lens at all six mature checkpoints; three additional screenshots show selected-point coordination, full-domain context, and maximized views. The PNGs are 1912 x 1080 because the in-app browser content area excludes its outer chrome.

- The fixed red-up/blue-down palette makes strengthening descent and persistent ascent immediately comparable through time; near-neutral cells remain white.
- Plan and section axes preserve their physical aspect within each coordinated panel. Storm and full-domain payload extents match the actual displayed native cells.
- Cloud-category opacity driven by condensate mass keeps weak species visible without turning the storm into a solid categorical mask.
- Compact vertical legends leave room for the scientific views while retaining units, frame extrema, fixed-scale status, and overlay keys.
- Rain, reflectivity, UH, vorticity, and flow outlines remain distinguishable at default settings.
- At late times, the Cloud and Precipitation plan is dominated by hail-treated large ice; this is scientifically honest for the retained field but requires the exact label and selected-point species values.
- Full-domain context confirms the primary storm remains interior, but the one-kilometer display is intentionally sparse at that scale.

## 12. Scientific interpretation limits

- Native coordinates and winds are in a translating model frame; ground-relative horizontal wind adds `(12.5, 3.0)` m/s.
- Histories are 15 minutes apart; no continuous process path is shown.
- Secondary convection is visible, but split lineage and causal relationships are unresolved.
- The 15-20 km Rayleigh layer overlaps upper storm structure; causal influence is not diagnosed.
- `dbz` is modeled reflectivity, not radar observation.
- Hydrometeor categories are modeled mass fields, not literal particle appearance.
- `qg` is a hail-configured large-ice category, not proof of hail occurrence or impact.
- Low-level motion, rain, pressure, and flow do not establish a thermodynamic cold pool without suitable temperature or buoyancy evidence.
- No tornado, hazard, forecast, observed-storm correspondence, or paper-figure equivalence is claimed.

## 13. Usability and performance

At final head, warm and cold selected-frame requests on the local retained data measured:

| Viewport | Payload range | Response range |
|---|---:|---:|
| Storm region | 324-379 kB | 0.09-0.14 s |
| Full domain | 803-983 kB | 0.13-0.24 s |

The reader validates the retained inventory once per artifact fingerprint, then opens only one selected history per request. Cropping happens server-side and sections retain full-grid indices for honest selection. Browser loading, failure, retry, and unsupported retained-output states are explicit. Playback, Lens switching, viewport switching, selected-point coordination, Context collapse/restore, and maximize/restore were exercised in the live desktop browser.

The payload is practical for this one retained benchmark. A production World should consider compact binary or tiled numeric transport before multiplying these matrices across simulations; Gate C does not authorize that architecture.

## 14. Shared vocabulary implications

Existing terms remain sufficient: Cloud World, Simulation, Lens, Explore, timeline, inspector, and viewport all fit without semantic revision. `Storm region` and `Full domain` are clearer here than borrowing Mountain Waves' Focus/Full labels. `Lens` remains a coherent reasoning mode rather than a variable picker.

No new controlling term is required. **PM decision required:** Gate D must decide the final World identity, reference-Simulation framing, and whether these provisional Lens names survive product definition.

## 15. Unresolved questions and rejected concepts

- **Unresolved:** whether a later retained configuration with near-surface temperature or buoyancy should support a true cold-pool Lens.
- **Unresolved:** whether a production experience should offer model-relative/ground-relative wind switching.
- **Unresolved:** whether a more carefully bounded echo-top or cloud-top diagnostic adds understanding despite damping-layer overlap.
- **Rejected for first version:** number concentrations, automatic storm objects, split tracks, tornado/hail diagnosis, hazard guidance, synthetic particles, and a general variable catalog.
- **Rejected for Gate C:** 3-D storm rendering, a permanent World route, Recipe, variation model, linked navigation, and framework extraction.
- **PM decision required:** which of the three candidates, if any, define the first World increment and how the idealized benchmark is introduced to users.

## 16. Recommended Gate D decision inputs

Gate D now has evidence to decide:

1. the World identity and concise user promise without naming an unearned permanent category;
2. whether the exact official benchmark is the reference Simulation;
3. whether all three provisional Lenses belong in the first increment or one is deferred;
4. the approved default Lens, viewport, checkpoint, and overlay set;
5. how moving-frame winds, 15-minute cadence, secondary cells, large-ice language, and damping overlap remain visible;
6. whether low-level thermodynamic evidence is required before any future cold-pool scope;
7. the bounded production transport and caching work needed for responsive playback.

Gate C does not create Gate D or make these decisions.

## 17. Final disposition

`advance_to_storms_world_definition`

The retained benchmark supports multiple compelling and coherent examination experiences that reveal process relationships rather than merely presenting model fields. They are materially different from Trade Cumulus and Mountain Waves, scientifically bounded, usable across the complete mature sequence, and practical at the measured cost. Gate D has sufficient evidence to decide World identity, reference Simulation, first Lenses, and implementation scope.
