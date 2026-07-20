# Surface Flux Control Evidence Status

**Status:** Current descriptive implementation status and qualified research
evidence

This document records verified current facts about the observed-sounding
surface-flux path and qualifies the historical campaign evidence. The original
mixed validation and implementation-decision record is preserved in the
[archive](../archive/research/surface-flux-control-validation-legacy.md).

## Implemented Path

[PR #308](https://github.com/coloradotim/cloud-chamber/pull/308) implemented
numeric constant uniform surface heat and moisture controls for the
observed-sounding path.

- The selected values are direct CM1-facing proxy controls:
  `cnst_shflx` in `K m/s` and `cnst_lhflx` in `g/g m/s`. They are not `W/m2`
  surface-energy-budget inputs.
- The forcing is uniform over the domain and constant through model time for
  this path.
- Package, run, and result metadata preserve the selected values, units, CM1
  values, and the `constant_uniform_surface_flux_proxy` boundary.
- This path is not a realistic land-surface, radiation, soil-hydrology,
  transpiration, wet-ground, terrain, or place/time energy-budget model.

## Research Evidence

- [`surface_forced_tall_001`](surface-forced-campaigns/surface_forced_tall_001.md)
  and
  [`surface_forced_tall_002`](surface-forced-campaigns/surface_forced_tall_002.md)
  are point-in-time research evidence, not current setup authority.
- The old three-second six-hour default path showed a terminal
  numerical-integrity failure upstream of ingest. The
  [lower-timestep restart probe](surface-forced-campaigns/surface_forced_tall_002_lower_timestep_restart_probe.md)
  crossed the prior failure window with finite output, providing bounded
  stability evidence only.
- The [final issue #336 PM
  disposition](https://github.com/coloradotim/cloud-chamber/issues/336#issuecomment-4995992707)
  retained the safer-timestep lesson but superseded the recommendation to run a
  full cold-start `surface_forced_tall_003` forensic campaign. That broader
  campaign is not planned.

## Boundaries

This evidence does not define canonical BOMEX, an approved Cloud World or
Recipe, a current campaign plan, or future product direction. It does not
prescribe new controls, runs, UI, or implementation work.
