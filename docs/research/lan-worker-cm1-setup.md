# Trusted LAN Worker CM1 Setup

Status: setup/validation note for #226

Cloud Chamber remains local-first. The MacBook is the system of record for the
app server, browser UI, runtime inventory, result notebook, ingest, diagnostics,
and Explore. A trusted LAN worker is only a CM1 compute appliance for heavier
solver execution.

This note documents the one-time setup, manual validation, and current
script-assisted package transfer workflow for a trusted LAN worker. It
intentionally avoids hostnames, usernames, IP addresses, SSH keys, and personal
paths.

## Architecture Boundary

```text
MacBook
  Cloud Chamber backend and frontend
  configured runtime home
  package generation
  result metadata / notebook
  output-product manifests
  ingest / diagnostics / Explore

Trusted LAN worker
  CM1 executable and local runtime support files
  temporary copied run packages
  heavy CM1 solver execution
  raw CM1 output generation before copy-back
```

The worker should not host the Cloud Chamber web app, expose the backend on the
LAN, ingest NetCDF directly into the notebook, or act as a network share for
Explore. Future automation should copy a generated package to the worker, run
CM1 there, and copy completed output/logs back into the MacBook runtime home
before normal ingest.

## Security Assumptions

- The worker is a trusted machine on the same LAN.
- SSH key authentication is already configured locally.
- The SSH alias is local-only, for example `<worker-ssh-alias>`.
- The worker is not exposed to the public internet for Cloud Chamber.
- No SSH private keys, hostnames, usernames, IP addresses, or known-host
  entries are committed.
- No interactive sudo should be required for normal CM1 runs.
- Generated packages, logs, NetCDF output, copied runtime files, and scratch
  folders stay outside git.

The real SSH alias should stay in `~/.ssh/config`; Cloud Chamber docs and future
app config should refer to a placeholder or local-only setting instead of
committing it.

## Local-Only Configuration Shape

Worker settings should live in an ignored local config file or environment
overrides, not committed repo files.

The preferred local file is:

```text
~/CloudChamber/lan-worker.json
```

Alternative repo-local development path:

```text
local-data/lan-worker.json
```

`local-data/` is gitignored. The home-runtime config path is outside the repo
entirely and is the least surprising day-to-day option.

Config file shape:

```json
{
  "host": "<worker-ssh-alias>",
  "worker_root": "<worker-scratch-root>",
  "cm1_exe": "<worker-cm1-run-dir>/cm1.exe"
}
```

Optional command overrides:

```json
{
  "host": "<worker-ssh-alias>",
  "worker_root": "<worker-scratch-root>",
  "cm1_exe": "<worker-cm1-run-dir>/cm1.exe",
  "cm1_env": {
    "OMP_NUM_THREADS": "16"
  },
  "cm1_command": "<optional launch command, defaults to cm1_exe>",
  "ssh": "ssh",
  "rsync": "rsync"
}
```

Environment overrides are still supported for temporary testing:

```text
CLOUD_CHAMBER_LAN_WORKER_HOST=<worker-ssh-alias>
CLOUD_CHAMBER_LAN_WORKER_ROOT=<worker-scratch-root>
CLOUD_CHAMBER_LAN_WORKER_CM1_EXE=<worker-cm1-run-dir>/cm1.exe
CLOUD_CHAMBER_LAN_WORKER_CM1_COMMAND=<optional launch command>
```

Optional future values:

```text
CLOUD_CHAMBER_LAN_WORKER_RSYNC=rsync
CLOUD_CHAMBER_LAN_WORKER_SSH=ssh
CLOUD_CHAMBER_LAN_WORKER_MAX_ACTIVE_RUNS=1
```

`scripts/lan-worker-run.sh` reads the first three required values. `cm1_env`
is exported before CM1 starts and is the preferred way to set CPU-threading
variables such as `OMP_NUM_THREADS`. `cm1_command` can be used for trusted
local launch forms such as `mpirun -np 4 <worker-cm1-run-dir>/cm1.exe`; it
defaults to `cm1_exe`. The `cm1_exe` value is still required because the script
uses its parent directory to stage CM1 runtime support files such as
`LANDUSE.TBL`.

The optional `ssh` and `rsync` config values can override command names or add
local-only flags. Environment variables override the JSON file when both are
present.

## Worker Performance Modes

The worker should not use a serial proof binary for normal Cloud Chamber runs.
Treat worker CM1 builds as explicit performance modes:

```text
serial proof:
  build target: gfortran without OpenMP
  use only for installation smoke tests

OpenMP CPU:
  build target: gfortran with -fopenmp and -DOPENMP
  config: cm1_env.OMP_NUM_THREADS set to the intended worker core count
  current recommended default for the trusted LAN worker

MPI / hybrid:
  build target: mpif90 and/or MPI plus OpenMP
  config: cm1_command such as "mpirun -np <n> <cm1.exe>"
  future validation path if OpenMP alone is not enough

OpenACC / GPU:
  requires a CM1 source tree and compiler path that actually support OpenACC,
  typically NVIDIA HPC SDK / nvfortran
  must be validated against CPU output before becoming a default
```

The CM1 r21.1 tree originally installed for Cloud Chamber includes NVIDIA
compiler stanzas in its Makefile but no OpenACC source/directive support. The
current upstream CM1 compile guide documents `USE_OPENACC=true` for PGI/NVHPC,
so GPU execution should be treated as a separate validated install/build path,
not as a flag that can be applied to the existing r21.1 serial binary.

Current worker-local recommended config shape:

```json
{
  "host": "<worker-ssh-alias>",
  "worker_root": "<worker-scratch-root>",
  "cm1_exe": "<worker-openmp-cm1-run-dir>/cm1.exe",
  "cm1_env": {
    "OMP_NUM_THREADS": "16"
  }
}
```

## Worker Filesystem Expectations

The worker needs:

- a built CM1 install with executable permission on `cm1.exe`;
- a known CM1 run directory containing runtime support files needed by the
  selected case, such as `LANDUSE.TBL`;
- a dedicated Cloud Chamber worker scratch root, for example
  `<worker-scratch-root>/runs/<run-id>/`;
- enough free disk for copied packages and CM1 output;
- normal shell utilities used by manual checks, such as `mkdir`, `du`, `find`,
  `tail`, `rsync`, or `scp`.

The worker scratch root should be disposable. It should not be the source CM1
install, the user's home directory root, the MacBook runtime home, or a repo
checkout.

## Script-Assisted Package / Run / Return Workflow

Cloud Chamber currently provides a script-assisted workflow for trusted LAN
worker execution:

```bash
scripts/lan-worker-run.sh start --package-dir <runtime-home>/runs/<run-id>
scripts/lan-worker-run.sh status --package-dir <runtime-home>/runs/<run-id>
scripts/lan-worker-run.sh collect --package-dir <runtime-home>/runs/<run-id>
```

The script expects the package to have been generated locally under
`<runtime-home>/runs/<run-id>/`. It validates that the package is inside the
local runtime home and contains:

```text
run_manifest.json
case_manifest.json
namelist.input
input_sounding
runtime_file_checklist.json
dry_run_report.json
```

`start` copies that package to:

```text
<worker-scratch-root>/runs/<run-id>/
```

It then launches CM1 on the worker in that copied package directory and writes:

```text
logs/stdout.log
logs/stderr.log
worker_status.json
worker_complete.marker or worker_failed.marker
```

`status` reads the worker-side `worker_status.json`.

`collect` copies the worker directory back to a local staging directory:

```text
<runtime-home>/runs/<run-id>.incoming/
```

After required returned files and worker status are verified, it promotes the
returned output/logs into the original local package directory and updates the
local `run_manifest.json` to the same completed/failed states used by local CM1
runs. Local ingest still happens on the MacBook; Results and Explore continue
to read MacBook-local files.

Generated `.incoming` staging folders are removed after successful promotion.
Failed collect attempts leave staging evidence for inspection.

## Worker Cleanup After Local Ingest

Worker output can be large. The worker copy should be cleaned up after:

1. copy-back to the MacBook succeeds;
2. the returned files are verified and promoted into the local runtime home;
3. local MacBook ingest succeeds, or the user explicitly decides the worker copy
   is no longer needed.

Cleanup is explicit and separate:

```bash
scripts/lan-worker-run.sh cleanup --package-dir <runtime-home>/runs/<run-id>
```

or:

```bash
scripts/lan-worker-run.sh cleanup --run-id <run-id>
```

Cleanup only targets:

```text
<worker-scratch-root>/runs/<run-id>/
```

It refuses empty run IDs, path traversal, path separators, the worker root
itself, the worker runs root itself, and paths inside the configured CM1 install
directory. If the worker run directory has already been removed, cleanup reports
that it is already clean instead of invalidating the local result.

Cleanup failure after successful copy-back does not change the local completed
result or ingest record. The local `worker_status.json` records
`worker_cleanup_failed` so cleanup can be retried later.

## Bootstrap A Fresh Ubuntu Worker

If the worker does not already have CM1 built, set up the compiler and NetCDF
toolchain first. On an Ubuntu worker, the expected one-time setup is:

```bash
ssh <worker-ssh-alias> '
  sudo apt-get update &&
  sudo apt-get install -y build-essential gfortran libnetcdf-dev libnetcdff-dev netcdf-bin rsync
'
```

Then confirm the build tools exist:

```bash
ssh <worker-ssh-alias> '
  command -v gcc &&
  command -v gfortran &&
  command -v make &&
  test -f /usr/include/netcdf.h &&
  ldconfig -p | grep -q libnetcdff &&
  echo "OK: compiler and NetCDF Fortran toolchain"
'
```

If the CM1 source is already available on the MacBook, copy a clean CM1 release
tree to the worker. Do not copy generated CM1 output. A safe first transfer
shape is:

```bash
rsync -av \
  --exclude 'run/cm1.exe' \
  --exclude 'run/onefile.F' \
  --exclude 'run/cm1out*' \
  --exclude 'run/stats*' \
  --exclude 'run/*.nc' \
  --exclude 'run/logs/' \
  <local-cm1-source-root>/ \
  <worker-ssh-alias>:<worker-cm1-root>/
```

The copied tree should include CM1 source files, `src/Makefile`, `README.*`
files, `run/config_files/`, and static runtime lookup/data files. It should not
include old run output.

On the worker, adapt the copied Makefile for Ubuntu NetCDF paths and build the
single-process GNU executable:

```bash
ssh <worker-ssh-alias> '
  cd <worker-cm1-root>/src &&
  cp Makefile Makefile.cloud-chamber-worker-backup &&
  python3 - <<'"'"'PY'"'"'
from pathlib import Path
import re

path = Path("Makefile")
text = path.read_text()
text = re.sub(r"^NETCDF\\s*=.*$", "NETCDF = /usr", text, count=1, flags=re.MULTILINE)
path.write_text(text)
PY
  make clean || true &&
  make
'
```

Successful compilation should create:

```text
<worker-cm1-root>/run/cm1.exe
<worker-cm1-root>/run/onefile.F
```

Verify:

```bash
ssh <worker-ssh-alias> '
  test -x <worker-cm1-root>/run/cm1.exe &&
  test -f <worker-cm1-root>/run/onefile.F &&
  echo "OK: CM1 built on worker"
'
```

If the Makefile does not contain an active `NETCDF = ...` line, edit it
manually so the active NetCDF section points at the worker's NetCDF install,
normally:

```make
NETCDF = /usr
OUTPUTINC = -I$(NETCDF)/include
OUTPUTLIB = -L$(NETCDF)/lib
OUTPUTOPT = -DNETCDF -DNCFPLUS
LINKOPTS  = -lnetcdf -lnetcdff
```

The active hardware section for the first worker proof should be the
single-process GNU compiler section:

```make
FC   = gfortran
OPTS = -ffree-form -ffree-line-length-none -O2 -finline-functions -fallow-argument-mismatch
CPP  = cpp -C -P -traditional -Wno-invalid-pp-token -ffreestanding
```

MPI/OpenMP worker builds can come later. The first goal is a known-good
single-process executable that can run a basic case.

## Basic Validation Case

The first validation should use a basic CM1 case that is already known to run on
the worker independent of Cloud Chamber automation.

Acceptable validation options:

1. A CM1 reference case copied or prepared on the worker.
2. A Cloud Chamber-generated package copied manually to the worker.

For the first proof, the important evidence is not the scientific result. The
important evidence is:

- the worker can start `cm1.exe`;
- stdout/stderr are captured;
- CM1 terminates normally or fails with an understandable CM1/config error;
- CM1 output/log files are produced in the expected worker run directory;
- the MacBook can copy a small file to and from the worker over SSH.

Generated output from this validation must not be committed.

## Manual Validation Checklist

Run these from the MacBook unless a step explicitly says "on worker".

### 1. Confirm SSH Alias

```bash
ssh <worker-ssh-alias> 'hostname; pwd'
```

Expected evidence:

- SSH connects without interactive password prompts beyond normal key
  unlocking;
- the command prints the worker hostname and a working directory;
- no secrets or private key material are printed or saved.

### 2. Confirm Worker Scratch Root

```bash
ssh <worker-ssh-alias> 'mkdir -p <worker-scratch-root>/runs && test -d <worker-scratch-root>/runs && echo OK'
```

Expected evidence:

- the command prints `OK`;
- the directory is under a dedicated worker scratch root.

### 3. Confirm CM1 Executable And Runtime Files

```bash
ssh <worker-ssh-alias> 'test -x <worker-cm1-run-dir>/cm1.exe && echo OK: cm1.exe'
ssh <worker-ssh-alias> 'test -f <worker-cm1-run-dir>/LANDUSE.TBL && echo OK: LANDUSE.TBL'
```

Expected evidence:

- `cm1.exe` exists and is executable;
- required runtime support files for the validation case are present.

If a case uses another runtime file, add it to the worker checklist before
running CM1.

### 4. Confirm Small File Transfer

```bash
printf 'cloud-chamber worker transfer check\n' > /tmp/cloud-chamber-worker-check.txt
rsync -av /tmp/cloud-chamber-worker-check.txt <worker-ssh-alias>:<worker-scratch-root>/
rsync -av <worker-ssh-alias>:<worker-scratch-root>/cloud-chamber-worker-check.txt /tmp/cloud-chamber-worker-check-returned.txt
cmp /tmp/cloud-chamber-worker-check.txt /tmp/cloud-chamber-worker-check-returned.txt
rm -f /tmp/cloud-chamber-worker-check.txt /tmp/cloud-chamber-worker-check-returned.txt
ssh <worker-ssh-alias> 'rm -f <worker-scratch-root>/cloud-chamber-worker-check.txt'
```

Expected evidence:

- `rsync` succeeds in both directions;
- `cmp` exits successfully;
- the temporary transfer file is removed on both machines.

`scp` is acceptable if `rsync` is unavailable, but future automation should
prefer `rsync` because it gives better incremental copy behavior and clearer
file lists.

### 5. Run A Basic CM1 Case On Worker

On the worker, prepare or copy a validation case into:

```text
<worker-scratch-root>/runs/<validation-run-id>/
```

Then run from that package directory:

```bash
ssh <worker-ssh-alias> '
  cd <worker-scratch-root>/runs/<validation-run-id> &&
  <worker-cm1-run-dir>/cm1.exe > stdout.log 2> stderr.log
'
```

Expected evidence:

- `stdout.log` and `stderr.log` are produced in the worker validation run
  directory;
- CM1 output files appear in the same run directory or configured output
  location;
- if the case completes, the exit code is `0`;
- if the case fails, the failure is a CM1/config issue rather than SSH,
  permissions, missing executable, or missing runtime-file setup.

Inspect without copying output into the repo:

```bash
ssh <worker-ssh-alias> '
  cd <worker-scratch-root>/runs/<validation-run-id> &&
  tail -80 stdout.log &&
  tail -80 stderr.log &&
  find . -maxdepth 2 -type f \( -name "*.nc" -o -name "cm1out*" -o -name "stats*" -o -name "*.ctl" -o -name "*.dat" \) -ls &&
  du -sh .
'
```

### 6. Confirm Copy-Back Path

For validation, copy back only a tiny harmless evidence file, not full NetCDF
output:

```bash
rsync -av <worker-ssh-alias>:<worker-scratch-root>/runs/<validation-run-id>/stdout.log /tmp/cloud-chamber-worker-stdout.log
tail -20 /tmp/cloud-chamber-worker-stdout.log
rm -f /tmp/cloud-chamber-worker-stdout.log
```

Expected evidence:

- MacBook can copy worker run artifacts back over SSH;
- full generated CM1 output remains outside git unless a future automation
  explicitly copies it into the MacBook runtime home.

## What Tim Needs To Provide Before Automation

An existing SSH alias is enough for the SSH alias requirement if it works
non-interactively from the MacBook shell. Before Cloud Chamber can automate the
trusted-worker path, it still needs local answers to:

1. Permission to install the Ubuntu build prerequisites if they are missing:
   `build-essential`, `gfortran`, `libnetcdf-dev`, `libnetcdff-dev`,
   `netcdf-bin`, and `rsync`.
2. A clean CM1 source tree to copy to the worker, or permission to copy the
   existing local CM1 source tree while excluding generated output.
3. Worker CM1 executable path after build:
   `<worker-cm1-root>/run/cm1.exe`
4. Worker CM1 run directory containing required runtime files:
   `<worker-cm1-root>/run`
5. Dedicated worker scratch root:
   `<worker-scratch-root>`
6. Confirmation that `rsync` or `scp` works both directions.
7. Confirmation that a basic CM1 case runs manually on the worker.
8. Approximate worker disk budget for copied packages and output.
9. Whether only one worker CM1 run should be active at a time for the first
   automation pass.

Do not send or commit SSH private keys. If a future config file is needed, it
should live under the local Cloud Chamber runtime home or environment, and it
must stay gitignored.

## Future Automation Boundary

This setup note is the prerequisite for a later package-run-return issue.
Future automation should preserve this sequence:

```text
MacBook generates package
-> copy package to worker scratch
-> worker runs CM1 in copied package
-> copy output/logs back to MacBook runtime home
-> MacBook ingests output
-> Results / Explore use MacBook-local data
```

Future automation should not:

- mount worker output directly into Explore;
- require network shares for ingest;
- expose the Cloud Chamber backend over the LAN;
- run CM1 in CI;
- commit generated worker output;
- make the trusted worker required for normal local use.

## PR Validation Evidence Template

When manual worker validation is performed, record only summary evidence in the
PR body or local notes. Do not commit logs or output.

```text
SSH alias checked:
Worker scratch root:
Worker CM1 executable:
Required runtime files checked:
Validation case:
Exit code:
Output evidence:
Transfer check:
Caveats:
Generated artifacts committed: no
```
