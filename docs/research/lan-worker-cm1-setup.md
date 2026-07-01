# Trusted LAN Worker CM1 Setup

Status: setup/validation note for #226

Cloud Chamber remains local-first. The MacBook is the system of record for the
app server, browser UI, runtime inventory, result notebook, ingest, diagnostics,
and Explore. A trusted LAN worker is only a CM1 compute appliance for heavier
solver execution.

This note documents the one-time setup and manual validation expected before
Cloud Chamber automates package transfer, remote launch, or return-copy flows.
It intentionally avoids hostnames, usernames, IP addresses, SSH keys, and
personal paths.

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

Future automation should read worker settings from local environment variables
or ignored local config, not committed repo files.

Recommended local-only values:

```text
CLOUD_CHAMBER_LAN_WORKER_HOST=<worker-ssh-alias>
CLOUD_CHAMBER_LAN_WORKER_ROOT=<worker-scratch-root>
CLOUD_CHAMBER_LAN_WORKER_CM1_EXE=<worker-cm1-run-dir>/cm1.exe
CLOUD_CHAMBER_LAN_WORKER_CM1_RUN_DIR=<worker-cm1-run-dir>
```

Optional future values:

```text
CLOUD_CHAMBER_LAN_WORKER_RSYNC=rsync
CLOUD_CHAMBER_LAN_WORKER_SSH=ssh
CLOUD_CHAMBER_LAN_WORKER_MAX_ACTIVE_RUNS=1
```

These are examples of the expected shape, not implemented settings in this
setup note.

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
