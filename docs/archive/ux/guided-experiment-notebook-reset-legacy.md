# UX Reset: Guided Experiment Notebook

> **Archive status:** This historical/superseded document is preserved for project history. It does not establish current product direction, recipe status, roadmap priority, or MVP scope.

## 1. Summary

Cloud Chamber's user-facing UX direction is:

```text
Cloud Chamber is a guided experiment notebook for understanding why clouds formed, failed, stayed shallow, or grew stronger.
```

This document records PM direction for future UX work. Codex does not make
product or design decisions here; it implements documented PM direction from
the relevant issue or doc.

The reset keeps the scientific and CM1 pipeline work intact, but changes what
the primary app surface should emphasize. The user-facing model is guided
experiments, an experiment notebook, focused visualization, a prominent `What
happened here?` Explore interaction, plain-language explanation, comparison
between variants, and technical details on demand.

## 2. Why The Reset Is Needed

The current product surface exposes too much internal diagnostic scaffolding.
The underlying CM1, ingest, diagnostics, selected-region, comparison, and
visualization work remains valuable, but the visible app structure should not
feel like a diagnostic cockpit.

The product problem is not a lack of diagnostics. The product problem is that
the internal diagnostic model is showing through as the visible app structure.

Future UX work should make the first-read experience simpler, more readable,
and more worth reopening without hiding the technical truth when the user asks
for it.

## 3. User-Facing Product Frame

Use this exact top-level frame:

```text
Cloud Chamber is a guided experiment notebook for understanding why clouds formed, failed, stayed shallow, or grew stronger.
```

Primary user-facing concepts:

```text
Guided experiments
Experiment notebook
Focused visualization
What happened here?
Plain-language explanation
Comparison between variants
Technical details on demand
```

Primary screens should start from the experiment story, outcome,
visualization, and next action. They should not start from implementation
surfaces, raw run folders, source-field tables, or process taxonomy menus.

Explore should make the most compelling Cloud Chamber interaction obvious:

```text
Click a spot or region in a completed cloud result
-> ask What happened here?
-> get a clear explanation backed by CM1-derived diagnostics
```

## 4. Thermal Fate Behind The Curtain

Thermal Fate remains the internal scientific diagnostic and explanation model.

Thermal Fate should power:

```text
explanations
confidence/caveat labels
comparison summaries
selected-region diagnostics
technical provenance
```

Thermal Fate should not dominate the primary visible UI as a process-taxonomy
cockpit.

Selected-region diagnostics are not being discarded. They power the
user-facing `What happened here?` explanation: the user selects a cloud,
updraft, clear-air thermal, or no-cloud region, and the app explains what
happened there, what evidence supports it, and what is still uncertain.

The frontend should present backend-supported diagnostics, confidence, and
caveats. It should not expose the Thermal Fate taxonomy first, and it should
not invent scientific explanations.

The user should still be able to inspect technical evidence, caveats, native
fields, and provenance. Those details belong in the technical layer, generally
behind disclosure or other on-demand patterns.

## 5. Workspace Contracts: Build / Results / Explore

Keep the three top-level workspaces:

```text
Build
Results
Explore
```

Define them this way:

```text
Build:
  Choose/setup a guided experiment and safely create/launch a local CM1 package.

Results:
  The experiment notebook and comparison home.

Explore:
  A focused visualization plus explanation screen for one selected result.
  The core interaction is "What happened here?" -- select a cloud, updraft,
  clear-air thermal, or no-cloud region and receive a CM1-backed explanation of
  what happened there and why.
```

Build should feel like guided experiment setup, not a form-first namelist
editor.

Results should feel like the experiment notebook: what was run, what happened,
what is worth saving, and how variants compare.

Explore should focus on one selected result at a time: what it looks like, what
the outcome means, what happened in a selected region, and what technical
evidence is available if requested.

## 6. Information Hierarchy: Primary / Secondary / Technical

Every primary screen should use this hierarchy:

```text
Primary layer:
  user-facing experiment story, outcome, visualization, and next action

Secondary layer:
  controls and concise evidence needed to understand the result

Technical layer:
  raw IDs, native grids, source variables, provenance, caveats, output counts, detailed diagnostics
```

Technical-layer content must remain available. It should generally move behind
details, disclosure, drawer, or equivalent on-demand patterns instead of
dominating the first read.

## 7. Screen-Level Direction

### Build

Build is for choosing and setting up a guided experiment, then safely creating
and launching a local CM1 package.

The primary read should be:

```text
What experiment am I setting up?
What atmospheric question does it answer?
What variant/control am I changing?
What will happen next?
```

Raw namelist settings, run IDs, generated file lists, and low-level provenance
belong in the technical layer.

### Results

Results is the experiment notebook and comparison home.

The primary read should be:

```text
What experiments exist?
What happened in each one?
Which results are worth saving?
How do variants compare?
What should I open next?
```

Results should emphasize experiment names, outcomes, notebook edit state,
plain-language diagnostics, and comparison between variants. Raw output counts,
run IDs, lifecycle/product state values, source-field tables, and full caveat
lists belong in the technical layer.

### Explore

Explore is a focused visualization plus explanation screen for one selected
result.

The primary read should be:

```text
What does this result look like?
What field/outcome am I seeing?
Why did this cloud form, fail, stay shallow, or grow stronger?
What should I inspect next?
```

Explore should not start as a grid/source-field cockpit. It should make the
visualization and plain-language explanation readable first, with concise
evidence and technical details available on demand.

Desired Explore flow:

```text
Open a result in Explore
-> see the main 2-D or 3-D visualization
-> click a cloud, updraft, clear-air thermal, or no-cloud region
-> the app marks the selected spot or region
-> the explanation panel answers what happened, what evidence supports it, and what is still uncertain
```

The explanation panel should be able to answer, when supported by backend
diagnostics:

```text
Did air rise here?
Did cloud water form here?
When did cloud first appear here?
How high did the cloud get here?
Did it stay shallow, grow, stall, or fade?
Was the area moisture-limited, cap-limited, or still uncertain?
How does this spot compare with the whole result or baseline?
What evidence supports this?
What evidence is missing?
```

The first implementation can start with 2-D selection if 3-D selection is too
hard. It may use existing selected-region diagnostics APIs when available.

## 8. What Moves Behind Disclosure

The following should generally move behind details, disclosure, drawer, or an
equivalent technical layer:

```text
raw variable names
native grid names
evidence tables
source-field tables
process taxonomy menus
run IDs
output file counts
technical caveats as first-read content
detailed diagnostics
full provenance labels
generated file lists
low-level lifecycle/product state strings
```

This does not mean hiding scientific honesty. It means the first-read UI should
lead with the experiment story and outcome, while technical evidence remains
available for trust and debugging.

## 9. Wording Guidelines

Use user-facing language first:

```text
guided experiment
experiment notebook
cloud formed
no cloud formed
What happened here?
Cloud formed here
Thermal without cloud
Cloud stayed shallow
Growth was limited
Evidence
Still uncertain
stayed shallow
grew stronger
rain detected
no rain detected
moisture-limited
cap-limited
saved / protected
not saved
technical details
```

Prefer plain-language explanations over process-taxonomy labels in primary UI.
Thermal Fate, native field names, grid names, and provenance terms can appear in
technical or advanced layers.

Avoid making these primary:

```text
raw variable names
native grid names
evidence tables
source-field tables
process taxonomy menus
run IDs
output file counts
technical caveats as first-read content
```

## 10. Manual QA Questions

Manual QA for this reset is qualitative only. It should answer:

```text
Does this screen make the experiment understandable?
Does the visualization feel physically plausible?
Does the page teach the right lesson?
Does the app feel like a tool worth reopening?
```

Objective behavior belongs in unit/component tests or Playwright, not a manual
checklist.

## 11. Implementation Sequencing

The immediate UX reset sequence is:

```text
#168 Codify Cloud Chamber UX reset decisions in product docs
-> #169 Fix Explore selected-result and field-loading trust states
-> #170 Refine Cloud Chamber navigation and layout style
-> #171 Redesign Results as a scan-friendly experiment notebook
-> #175 Make What happened here? the core Explore interaction
-> #172 Redesign Explore around one primary visualization and one explanation panel
-> #173 Redesign Build as guided experiment selection, not a form-first setup page
-> #112 Revisit renderer upgrade only after the simplified Explore UX is defined
-> #153/#154/#155 Future scenario-family expansion after the app is compelling and trustworthy
```

#172 depends on #175's interaction model. The Explore redesign should not
proceed as a generic visualization-plus-panel redesign without preserving
`What happened here?` as the center of the interaction.

Renderer upgrades and future scenario-family expansion should wait until the
simplified guided experiment notebook UX is defined and trustworthy.

## 12. Non-Goals

This reset doc does not:

- implement UI;
- choose colors, typography, spacing, renderer technology, or final visual
  design;
- redesign Results, Explore, or Build by itself;
- add scenario families;
- implement renderer upgrades;
- create broad manual QA spreadsheets or objective manual checklists;
- weaken CM1 provenance or scientific honesty.
