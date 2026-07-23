# Supercell Presentation Run Report

## Status

Issue #421 is active after the accepted Supercells World implementation in
issue #423 and merged PR #427.

Current state:

```text
source_and_product_contract_reviewed
presentation_configuration_selected
characterization_not_started
final_process_not_started
```

No issue #421 CM1 process had been started when this plan was recorded.

## Stable product identity

The presentation run will back the existing stable product identity:

```text
world_id: supercells
simulation_id: supercells_quarter_circle_reference
display_name: Quarter-Circle Supercell
```

The run does not create another built-in Simulation or a second Supercell
scientific setup.

## Accepted source

```text
source run: quarter-circle-supercell-official-20260722T142521Z
source case: cm1_r21_1_quarter_circle_supercell_official_v0
CM1 release: 21.1
official commit: 0f734f64efa89a684963a66d2ac32db67617912b
```

Gate B accepted the source run as a coherent persistent rotating supercell.
Gate C and the merged World implementation established the native fields needed
by Rotating Updraft, Cloud and Precipitation, and Low-Level Interactions.

## Selected presentation configuration

| Property | Gate B source | Presentation run |
|---|---:|---:|
| Domain | 120 x 120 x 20 km | unchanged |
| Grid | 120 x 120 x 40 | 240 x 240 x 60 |
| Horizontal spacing | 1,000 m | 500 m |
| Vertical spacing | 500 m | 333.333333 m |
| Scalar cells | 576,000 | 3,456,000 |
| Large timestep | 6 s | 3 s |
| Duration | 7,200 s | 10,800 s |
| Saved-output cadence | 900 s | 120 s |
| Saved histories | 9 | 91 |

The presentation run preserves the accepted analytic thermodynamic profile,
quarter-circle hodograph, deterministic warm bubble, translating frame,
boundaries, damping, numerics, and Morrison microphysics.

Presentation-driven changes are limited to:

- grid and timestep;
- duration and saved-output cadence;
- NetCDF output transport;
- a narrower retained output inventory.

## Output contract

Required three-dimensional fields:

```text
th prs qv
qc qr qi qs qg
nci ncs ncr ncg
dbz
uinterp vinterp winterp
xvort yvort zvort
```

Required two-dimensional fields:

```text
rain prate uh cref
```

The package disables native staggered `u`, `v`, and `w` duplicates, turbulence
output (`tke`, `km`, `kh`), and the unused stock swath fields. It retains total
potential temperature, pressure, and water vapor as a small thermodynamic
inspection margin without enabling a new Lens or cold-pool claim.

## Resource plan before execution

The final run has:

- six times the source scalar-cell count;
- three times the source integration work from timestep and duration;
- eighteen times the approximate integration workload before output overhead;
- 91 histories instead of 9.

The complete required numeric history floor is calculated without compression
credit. It is approximately 24.0 GB before NetCDF metadata, statistics, logs,
and reports. Launch requires that floor plus at least 5 GiB free.

The Gate B source completed in 552.652 seconds. Direct workload scaling gives an
initial final-run estimate near 2.8 hours before dense-output and mature-storm
overhead. The planning band is 3-6 hours.

One 300-second characterization process is authorized at the exact final grid,
timestep, and field inventory. It writes only the initial and 300-second
histories. Its sole purpose is to verify memory, field output, output size, and
measured cost before the full process. It is not a tuning run.

No automatic retry is authorized for either process.

## Pending evidence

After characterization:

- measured wall time;
- peak resident memory;
- actual history sizes;
- updated full-run runtime and storage projection;
- explicit final launch decision.

After the final process:

- exact runtime, retained size, and free-space remainder;
- complete history/time/field/unit/finite-value inventory;
- early, mature, and later storm evolution;
- matched Gate B comparisons;
- final Explore adoption and payload measurements;
- review packet and manual disposition.
