# Terrain-Aware Visualization Validation

## Status and decision boundary

Gate C implemented and validated the smallest browser path that can represent
the exact preserved Gate B dry mountain-wave output using physical
terrain-following geometry. The implementation is ready for manual
PM/scientific/visual review in a draft pull request.

The decision question was whether Cloud Chamber can represent the preserved
native CM1 terrain, physical field heights, staggering, time evolution, and
coordinate meaning honestly and at practical local cost. The answer for this
bounded dry two-dimensional result is yes.

This is not a Mountain Wave Clouds World. It does not approve moisture,
condensation, a lenticular-cloud case, a Recipe, Control, Lens, Comparison,
product navigation, three-dimensional terrain, or a generic terrain framework.
No CM1 process ran, no package was generated, and no scientific input changed.

## Preserved evidence identity

| Item | Value |
| --- | --- |
| Run ID | `dry-mountain-wave-official-20260721T183530Z` |
| Package/run implementation commit | `9ff73ff244c393bee2a2e93a851ad1ba2dc16287` |
| Gate B merge commit | `0fc006f0fcd34216b107a7c579cf4b679293ce44` |
| Histories | 11 numbered native files |
| Exact times | 0 through 2,160 s at 216 s cadence |
| Identity mode | pinned SHA-256 before and after every payload extraction |
| Verified inputs | 23 manifest, input, stats/log, and history files |

The endpoint calls the existing Gate B package loader and pinned identity
verifier before opening native output. It repeats the verifier after extraction
and rejects a changed hash set. The verifier also requires a completed,
zero-exit run and no active CM1 or MPI process. Manual validation used only this
preserved result; synthetic data was used only in automated tests.

## Prior flat-grid assumptions

The current shared visualization path cannot carry this result honestly:

- result field metadata records one-dimensional coordinate names and native
  dimensions, but not column-varying physical vertical geometry;
- the shared slice payload carries a rectangular value array and units, but not
  terrain, actual horizontal values, or a two-dimensional physical-height mesh;
- profiles and time-height products use one one-dimensional vertical
  coordinate;
- point-cloud construction combines independent one-dimensional x, y, and z
  coordinates;
- the frontend slice raster assumes an axis-aligned rectangular grid;
- Three.js placement uses independent axis extents and would turn singleton
  `y` into a misleading volume if used as the authoritative surface.

Passing this result through the shared path would flatten the atmosphere over
terrain. Gate C therefore adds a bounded research payload and unlinked route;
it does not modify flat-grid ingest, slices, point clouds, profiles,
time-height products, Explore, Comparison, or the Three.js viewer.

## Implemented data path

The backend route is:

```text
GET /api/research/mountain-wave-terrain?field=w&time_index=<0..10>
GET /api/research/mountain-wave-terrain?field=theta_perturbation&time_index=<0..10>
```

The response schema is `mountain_wave_terrain_research_v1`. Every response
contains the exact time sequence, selected native history, native x centers and
edges, terrain, physical scalar and full height meshes, nominal coordinates,
field values, dimensions, units, vertical staggering, fixed cross-time scale,
selected-time range, active-top evidence, vertical-reference semantics,
identity status, and extraction/serialization measurements.

The local inspection surface is:

```text
/research/mountain-wave-terrain
```

It is selected only from the exact local URL in `main.tsx`. It is not linked
from Home or Trade Cumulus and does not appear in product navigation. The view
opens on the final saved output so the central wave is immediately visible,
while previous/next, playback, and the slider expose all 11 exact histories.

## Geometry, height, and staggering

Native geometry remains authoritative:

- `xh` supplies scalar x centers and `xf` supplies cell edges;
- `zs(yh,xh)` supplies terrain at the singleton y row;
- `zhval(zh,yh,xh)` supplies native physical scalar-level height;
- physical full-level height is reconstructed from `zs`, nominal `zf`, and the
  verified active top using the CM1 r21.1 terrain transform;
- native `w(zf,yh,xh)` remains on physical full levels;
- native `th(zh,yh,xh)` remains on physical scalar levels.

The endpoint independently requires these active-top sources to agree:

| Source | Value |
| --- | ---: |
| Final nominal `zf` | 20,000 m |
| Runtime NetCDF `ztop` | 20,000 m |
| Configured `nz × dz` | `100 × 200 m = 20,000 m` |

The unchanged namelist text `ztop=18,000 m` is retained as inactive stretched-
grid configuration and is not used as the transform top. The full-level bottom
equals local terrain to 0.01 m tolerance and the full-level top is constant at
20,000 m across every x column. Native `zhval` must agree with independently
reconstructed scalar heights to 0.02 m.

The browser calls the vertical axis **Physical height (km)** and describes it
as geometric height above the model datum. It never calls this height MSL.
Hover identifies one native sample and reports its native `xh`, physical model
height on the field's actual level, nominal coordinate, and local height AGL:

```text
height AGL = physical field height - zs at the same native x cell
```

## Derivation, binning, and masking

`w` is native output in m/s. Potential-temperature perturbation is explicitly
derived in K as native `th` at the selected time minus native `th` in the same
scalar cell at `t=0 s`. No pressure field, contour, wind overlay, or horizontal
velocity collocation is exposed.

Native field values are never interpolated or collocated. Canvas cells are a
display binning of the native samples:

- scalar samples are painted between their surrounding physical full-level
  bounds;
- full-level `w` samples are painted between physical vertical midpoints, with
  the bottom and top clamped to terrain and the active top;
- interior horizontal display boundaries use the midpoint of neighboring
  physical center heights at the native `xf` edge;
- each polygon retains one unchanged native field value.

The horizontal midpoint operation affects only display geometry; it does not
resample a field. Tests exercise this edge construction directly. The terrain
polygon uses the same display edges, fills every pixel below terrain, and draws
an explicit dark terrain boundary. Cell construction rejects physical heights
below terrain, a bottom full level different from terrain, or a non-constant
top. Hover targets are the same above-terrain polygons, so no target exists
below terrain.

Each field uses a symmetric diverging scale fixed across all 11 times. The
scale does not change while stepping or playing:

| Field | Fixed scale | Final-time native range |
| --- | ---: | ---: |
| Vertical velocity `w` | -3.202856 to +3.202856 m/s | -3.094287 to +2.794157 m/s |
| Potential-temperature perturbation | -1.069580 to +1.069580 K | -1.066132 to +1.010071 K |

## Automated evidence

Focused backend tests use an intentionally curved three-column terrain fixture;
a flat-height implementation cannot satisfy its expected scalar/full meshes.
They verify:

- terrain, x, physical-height dimensions, and normalized units;
- non-flat physical levels over curved terrain;
- scalar versus full-level field dimensions and placement;
- final nominal `zf`, runtime `ztop`, and `nz*dz` agreement;
- failure on active-top mismatch;
- full-level bottom equal to terrain and constant physical top;
- exact 11-time ordering and failure on shifted times;
- singleton-`y` handling;
- failure when native `zhval` semantics are missing;
- finite fields and no physical geometry below terrain;
- local AGL and rejection of below-terrain AGL;
- explicit theta-perturbation derivation from the same `t=0` cell.

Focused frontend tests verify full-level midpoint bins, scalar full-level bounds,
continuous horizontal display edges, no below-terrain polygons, exact native
readout height/AGL, deterministic scale colors, exact-time requests, field
switching, dry singleton-`y` disclosure, and absence of a research link from
Home. Existing flat-grid tests remain in the full repository check and no
shared flat-grid implementation changed.

Focused verification passed:

```text
backend: 41 tests passed
frontend: 8 tests passed
frontend TypeScript/Vite build passed
frontend lint passed
backend Ruff and mypy passed
```

The final repository verification contract also passed:

```text
frontend: 124 tests passed
frontend TypeScript/Vite build and lint passed
backend: 581 tests passed
backend Ruff, mypy, script syntax, forbidden-artifact, and docs/data sanity checks passed
```

The known backend NumPy ABI runtime warning and Vite large-chunk warning remain
unchanged; neither is caused by this bounded path.

## Manual visual validation

The in-app browser loaded the live Vite frontend and FastAPI backend against the
exact preserved run. Validation inspected initial and final `w`, final theta
perturbation, every next-time transition from index 0 through 10, direct field
switching, playback, the pointer readout, and the payload/provenance disclosure.
Browser console errors and warnings were empty.

Observed results:

- the native domain spans -10 to +10 km at the x edges and 0 to 20 km in
  physical model height;
- the analytic bell ridge peaks at 400 m at native `x=100 m`, with the sampled
  terrain tapering to about 3.96 m near the domain edges;
- the atmospheric bottom follows that ridge and the dark below-terrain mask;
- no field polygon or hover target appeared below terrain;
- final `w` shows coherent alternating ascent/descent bands tilted downstream
  from the terrain through the central and upper domain;
- final theta perturbation shows corresponding coherent warm/cool tilted bands
  on scalar physical levels;
- the visible structures agree qualitatively with the Gate B native-output
  evidence without inventing a pass threshold;
- time and field changes preserve curved physical geometry and fixed scales;
- the pointer distinguishes native x, physical model height, local AGL, and
  nominal level;
- the page states **Dry 2-D x-z cross-section · singleton y** and presents no
  three-dimensional extrusion.

PM live review found the research surface strong as a first pass and confirmed
that the intended terrain-aware capability point was proven. Minor UI nits were
identified but do not affect this gate's geometry, semantics, or practical-use
decision and are not expanded into Gate C implementation work.

### Browser geometry record

| Item | Recorded value |
| --- | ---: |
| CSS viewport | 1,728 × 1,000 CSS px |
| `devicePixelRatio` | 2 |
| Browser zoom / visual viewport scale | 100% / 1 |
| Screenshot pixels | 1,728 × 1,000 px |
| Canvas CSS size | about 1,265 × 628 CSS px |
| Canvas backing store | 2,530 × 1,256 px |

The screenshot API returned CSS-sized 1,728 × 1,000 images even though the
canvas used a 2× backing store. Screenshot pixels were therefore recorded
separately and were not substituted for CSS viewport dimensions. Screenshots
were inspected at runtime and were not committed.

## Performance and practical cost

Representative final-time responses after process startup were:

| Field | Backend extraction | JSON serialization | Payload | HTTP request |
| --- | ---: | ---: | ---: | ---: |
| `w` | 132.7 ms | 2.2 ms | 556,371 bytes | 254.6 ms |
| theta perturbation | 108.1 ms | 2.4 ms | 526,139 bytes | 211.0 ms |

The first `w` request after a backend restart took 318.3 ms for extraction and
457.2 ms end to end; this cold-start value is reported rather than hidden.
Browser first meaningful render during the live pass was 484 ms. Measured field
switch latency was 300 ms and time-step switch latency was 266 ms. Playback
advanced on its 900 ms cadence without overlapping or skipped UI state.

The warmed FastAPI process resident set was about 68,192 KiB after representative
requests. Browser JavaScript heap telemetry was not exposed by the controlled
browser, so no browser-memory number is invented. The canvas backing store and
payload sizes are reported as the available browser-side memory evidence.

There is no decimation or cache. Each request validates all pinned files and
reads all 11 small histories to establish exact time order, stable geometry,
and a fixed cross-time field scale. This conservative research implementation
is practically usable for the preserved 100 × 100/101 result. A future shared
terrain contract should separate identity/geometry/scale caching from frame
values before attempting materially larger results.

## Cloud Chamber implications

This gate establishes only these bounded facts:

- the backend can carry column-varying physical scalar and full-level geometry
  without flattening it;
- the browser can draw native terrain-following topology, mask terrain, and
  provide scientifically precise native sample readout;
- the current machine can switch the preserved fields and times at practical
  local latency;
- a source-backed moist-case selection study is mechanically supportable.

It does not establish that the dry case forms clouds, that a moist reference
case exists, that the eventual experience should resemble this research UI, or
that generic terrain belongs in the product architecture.

## Limitations and unresolved questions

- The case is dry and cannot validate moisture, condensation, cloud water, or
  lenticular-cloud formation.
- `ny=1` validates only an authoritative two-dimensional cross-section, not a
  terrain volume or a 3-D atmospheric viewer.
- Only native `w` and derived theta perturbation are exposed. Pressure and
  horizontally staggered `u`/`v` are not part of this inspection surface.
- Horizontal physical cell edges are display midpoint geometry because native
  physical heights are supplied at x centers. Native field values are not
  interpolated.
- The payload rescans all 11 files per request. That is acceptable here but is
  not a scaling design for larger simulations.
- Future moist reference-case selection must determine whether source output
  provides enough terrain, moisture, cloud, and validation evidence. Gate C
  makes no selection.

No unresolved geometry, semantics, identity, visual, or practical-performance
defect blocks the bounded decision. Product design, shared-contract design, and
moist-case selection remain intentionally unresolved for later reviewed work.

## Final disposition

The exact preserved files remain hash-verified; terrain and both fields are
placed on physical native geometry; model height, nominal coordinate, and local
AGL are distinct; staggering and derivation are explicit; there is no fake
volume; the dry-wave evolution is visually interpretable; flat-grid behavior is
isolated; and local interaction is practical.

```text
advance_to_moist_reference_case_selection
```

This disposition authorizes only PM review and, if approved, a later research
issue to select a source-backed moist orographic-cloud case. It does not create
or activate Gate D.
