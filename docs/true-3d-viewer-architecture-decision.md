# True 3-D Viewer Architecture Decision

Issue: #112
Status: accepted for first implementation planning

## Decision summary

Cloud Chamber should implement a true 3-D Explore viewer after the current guided local experiment loop is stable enough to support it. The first implementation should be a real 3-D scene foundation, not a visual-polish sprint.

Recommended path:

```text
#112 architecture decision
-> #187 first true 3-D Explore viewer
-> #183 3-D vertical velocity layer
-> #193 visualization-quality CM1 run preset, if viewer evidence shows the need
-> #80 visual polish / export later
```

For the first true 3-D implementation, use **Three.js directly inside an isolated React component** rather than keeping the current CSS/HTML projection or adding a larger declarative 3-D abstraction immediately.

The first viewer should render:

- a real 3-D domain box;
- stable x/y/z orientation labels;
- a bounded `qc` cloud-water layer from backend-prepared point data;
- the current slice plane as a real 3-D object;
- a selected-point marker when the 2-D slice workflow selects a point;
- provenance labels that make clear the scene is a visualization of CM1-derived data.

Do not require higher-resolution CM1 output before building the viewer foundation. Current validated quick-look/standard results are enough to test interaction, scene geometry, labels, camera behavior, and data-contract boundaries. Higher output cadence or grid resolution should be evaluated later in #193 after the viewer reveals what is actually limiting visual quality.

## Product context

Cloud Chamber is a local cloud-physics lab, not a generic renderer demo. Explore should help the user understand one ingested CM1 result:

```text
3-D cloud context
-> synchronized slice inspection
-> selected-cell What happened here? explanation
```

The current fixed projection has served as a useful 2.5-D scientific instrument, but it should not be stretched into a pretend camera. A real 3-D scene is now justified because Build, Results, Storage, and unified Explore have clearer product roles.

## Goals for the first true 3-D viewer

The first implementation should answer:

- Where is cloud water in the CM1 domain?
- Where is the active slice plane?
- How does the 2-D slice relate to the 3-D scene?
- What selected point/cell is being explained?
- Can I rotate, pan, zoom, and reset the scene without losing orientation?

The first implementation should not try to answer every later renderer question. It is the scene foundation that later science layers can use.

## Options considered

### Keep current CSS/HTML projection

Pros:

- no new dependency;
- already integrated with current Explore tests;
- adequate for fixed side/top/oblique views.

Cons:

- not a real 3-D camera;
- hard to make orbit/pan behavior honest;
- label/axis behavior is already special-case heavy;
- future 3-D layers will keep fighting the projection model.

Decision: do not extend this as the next major viewer step.

### Custom Canvas/WebGL renderer

Pros:

- maximum control;
- smallest conceptual dependency surface if implemented carefully;
- can be tuned exactly to Cloud Chamber's data model.

Cons:

- more custom math and interaction code;
- higher implementation risk;
- browser tests become more bespoke;
- likely slower to reach a trustworthy first scene.

Decision: defer. This may be worth revisiting only if Three.js proves too heavy or constraining.

### Three.js directly inside React

Pros:

- real camera, scene, geometry, and controls without building WebGL primitives from scratch;
- clear imperative scene lifecycle can be isolated in one component;
- avoids coupling the first pass to a larger React-specific 3-D abstraction;
- easier to keep the app's existing React state model around selected result, time, field, and slice controls;
- enough for domain boxes, points/glyphs, planes, axes, labels, and markers.

Cons:

- requires careful React lifecycle cleanup;
- tests must focus on UI contracts and data mapping rather than WebGL pixels;
- future declarative scene complexity may eventually justify a different abstraction.

Decision: recommended first implementation path.

### React Three Fiber / declarative 3-D abstraction

Pros:

- idiomatic React component model for scene objects;
- potentially cleaner if the scene becomes a large interactive product surface;
- useful ecosystem for controls and helpers.

Cons:

- adds another abstraction before Cloud Chamber has proven the exact scene model;
- dependency/version compatibility should be verified at implementation time;
- can make low-level renderer/data-contract boundaries less obvious in the first pass.

Decision: do not choose it for the first true 3-D viewer. Revisit after #187 if the direct Three.js component becomes too large or hard to maintain.

### Volume rendering / ray marching / cinematic rendering

Pros:

- better cloud appearance potential;
- future demos and exports could look more impressive.

Cons:

- does not solve the immediate product need: honest spatial inspection and synchronized slices;
- higher GPU/browser complexity;
- harder provenance/caveat story;
- likely premature before scene foundation and 3-D science layers are stable.

Decision: defer to later visual-polish work. Not part of #187.

## Chosen first scene model

#187 should create a focused `True3DViewer` style component with a small scene contract:

```text
Scene root
  Domain bounds
  Axes / orientation labels
  Cloud-water qc layer
  Active slice plane
  Selected point marker, when available
  Camera controls
  Provenance/status labels outside or adjacent to the canvas
```

The scene should be driven by React state, but Three.js should own rendering inside the isolated component.

The 3-D scene should not own the scientific interpretation. It renders backend-prepared data and exposes the spatial relationship between cloud context, slice plane, and selected point. The existing `What happened here?` explanation remains driven by backend selected-region diagnostics and the 2-D slice selection workflow.

## Camera interaction model

#187 should implement:

- orbit;
- pan;
- zoom;
- reset camera;
- one useful default camera preset for shallow-cumulus inspection;
- stable labels that remain readable enough while the camera moves.

Do not add many camera presets in the first PR. Start with default + reset. Preserve room for later side/top/science presets if needed.

## Data contract guidance

The browser must not parse raw NetCDF.

For the first implementation, prefer reusing current backend visualization-ready payloads:

- field catalog;
- scalar point-cloud payloads;
- slice payloads;
- selected-region diagnostics payloads.

Only add or change backend endpoints if the current payloads are missing essential scene information such as domain extents or stable coordinate metadata.

The first scalar layers can remain thresholded point rendering or a surface-floor
layer for surface rain. They do not need isosurfaces, opacity approximation, or
volume rendering. Coordinate extents, units, thresholds, max point counts,
selected-field min/max/mean stats, downsampling notes, and provenance/caveats
should remain visible or available on demand.

## Relationship to vertical velocity

Do not fold #183 into #187 by default.

#187 should establish the scene, camera, labels, slice plane, and initial scalar
field layer. Later field-layer work can add supported scalar views such as
`qc`, `qr`, `qv`, `dbz`, and surface `rain` when the backend can provide
trustworthy visualization-ready payloads. #183 should still remain separate for
signed `w` updrafts and downdrafts, because vector/signed-motion fields need
their own representation and should not be hidden inside a generic scalar layer.

This sequencing matters because vertical velocity needs its own data contract and visual defaults. It should not be hidden inside the base viewer PR.

## Relationship to higher-resolution or visualization-quality runs

Do not require higher-resolution CM1 runs before #187.

Current validated quick-look and standard results are sufficient to test whether the viewer works. Higher-resolution model output should wait until the viewer reveals the actual limitation:

- sparse points may be a threshold/downsampling issue;
- jumpy evolution may be output cadence;
- blocky structure may be grid resolution;
- sluggish browser behavior may be payload size or rendering strategy.

#193 should evaluate visualization-quality presets later. Start with output cadence before changing grid resolution unless evidence says otherwise.

## Testing strategy

For #187, automated tests should focus on objective behavior, not pixel-perfect 3-D appearance.

Component tests should cover:

- viewer shell renders for a selected result;
- camera controls are present;
- reset camera action is available;
- domain/axis labels render;
- cloud-water layer state/provenance renders;
- slice plane receives orientation and position state;
- selected-point marker renders when selection exists;
- missing-field/no-cloud states remain trustworthy.

Playwright tests should cover:

- Results -> Explore opens the true 3-D viewer;
- camera controls are reachable at desktop viewports;
- slice orientation/position changes keep the 3-D plane and 2-D slice synchronized;
- selected slice cell still drives `What happened here?`;
- no layout overlap at approximately 1470 x 956 and 1720 x 1440;
- Dry Failed/no-cloud result does not look like a broken viewer state.

Manual QA should judge:

- spatial plausibility;
- orientation clarity;
- whether the 3-D scene helps the slice/explanation workflow;
- whether the viewer feels like a scientific instrument rather than a renderer demo.

## Non-goals for #187

Do not include:

- 3-D `w` / updraft / downdraft layer, unless #112 is intentionally revised later;
- arbitrary 3-D point picking;
- volume rendering;
- ray marching;
- cinematic lighting;
- fly-through;
- video/still export;
- new scenario families;
- higher-resolution CM1 run presets;
- real CM1 execution in CI;
- committed screenshots, traces, NetCDF output, logs, runtime folders, or generated visual artifacts.

## Implementation prompt for #187

Use this decision as the controlling product/architecture direction for #187:

```text
Implement the first true 3-D Explore viewer using direct Three.js inside an isolated React component. Preserve the existing Results -> Explore workflow, existing 2-D slice inspector, and What happened here? explanation path. Render the current qc cloud-water context, domain bounds/axes, synchronized slice plane, selected-point marker, and provenance labels. Add orbit/pan/zoom/reset camera behavior. Do not add vertical velocity layers, volume rendering, cinematic polish, freeform 3-D selection, or higher-resolution run presets. Use backend visualization-ready data only; do not parse raw NetCDF in the browser. Add component and Playwright coverage and collect uncommitted screenshots for 1470 x 956 and 1720 x 1440 review.
```
