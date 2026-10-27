# Local and cloud VM deployment

## Local review

The default Compose setup binds the dashboard only to the local loopback address
on port 4207. It runs one Prefect server and one serving process. SQLite is used
for this small, single-server assignment lab; the code and public dataset are
baked into the image and runtime state lives in named volumes.

Start with `docker compose up --build -d`. Wait for server health and two
completed cycles, then run `docker compose exec runner python -m src.verify
--wait-scheduled`. Inspect the dashboard logs and tables rather than relying only
on a successful container start.

Stop with `docker compose down`. Avoid `down --volumes` while evidence is needed.
Never use a broad container cleanup command that affects other coursework.

## Cloud VM option

No cloud resources are provisioned by this repository. If cloud deployment is
chosen, use an existing Linux VM with Docker Engine and the Compose plugin,
adequate memory for the Python packages, and an SSH account.

1. Transfer this checkout to the VM. Record the source commit and source hashes.
2. Create `.env` from `.env.example` and set `ASSIGNMENT_ENVIRONMENT=cloud`.
   Keep `PREFECT_UI_API_URL=http://127.0.0.1:4207/api` for the tunnel below.
3. Run `docker compose up --build -d` on the VM.
4. From the reviewing laptop, run `ssh -L 4207:127.0.0.1:4207 USER@VM_HOST`.
   Replace USER and VM_HOST with the actual SSH account and host.
5. Open `http://127.0.0.1:4207` on the laptop. Traffic travels through the SSH
   tunnel; no public application port needs to be opened.
6. Capture the cloud provider's VM identity/status, the VM's Compose status, the
   running dashboard and at least two scheduled completed cycles. The browser's
   localhost URL reflects the tunnel and is not by itself cloud proof.
7. Run the verification command on the VM and export the output folder.
   Preserve timestamps and hashes alongside the dashboard screenshots.
8. Review the evidence before setting `cloud_evidence_confirmed` in group.json.

Use `docker compose down` on this project when the demonstration is over. Stop
any cloud resources through the chosen provider when no longer needed; stopping
the containers does not stop VM billing.

## BITS Prayogshala virtual lab

The CCZG506 virtual lab advertises Python and Prefect. The separate CCZG506D
console lab provides AWS services and has its own credit quota. For the virtual
lab, put the checkout and its Python runtime inside `~/workspace`; only this
folder persists after shutdown. System installations and Docker's default named
volumes may be lost. Inspect the actual machine before choosing an installer.

The inspected VM runs Rocky Linux 9.5 and its persistent workspace is NFS4.
**Do not put the live SQLite database in this workspace.** Prefect enables WAL,
which [SQLite does not support on a network filesystem](https://www.sqlite.org/wal.html).
The native launcher rejects that configuration before starting services. A
longer startup timeout does not fix this storage incompatibility.

Use a private PostgreSQL server and set `PREFECT_SERVER_DATABASE_CONNECTION_URL`
in the launching shell, keeping credentials out of source control and logs.
PostgreSQL permits an NFS data directory only with the `hard` mount requirement;
verify that condition before initialization and retain normal fsync/durability
settings. See [PostgreSQL storage requirements](https://www.postgresql.org/docs/17/creating-cluster.html).
Keep the database, runtime and project evidence inside `~/workspace`. PostgreSQL
setup passed a private application-role connection check on the lab. On 26
October 2026, Prefect returned HTTP 200 and all 14 functional checks passed,
including at least two completed scheduled parent workflows at the 120-second
interval. Five cloud dashboard screenshots were captured and inspected on 26
October 2026; see [the capture record](../evidence/cloud-prayogshala-20261026/README.md).
The frozen data, models, API and verification archive has been imported and its
inventory hashes verified. A later restart and graceful shutdown also passed;
the same capture record links the lifecycle result and its separate provenance.

Provisioning checkpoint, 26 October 2026:
- The original workspace is a **soft** NFS mount. Changing it in place failed.
  A separate mount of the same user workspace at `~/workspace/.assignment1-durable`
  with `hard,nosharecache` passed inspection. Access the database exclusively
  through that mount; do not access it concurrently through the original mount.
- Enabled Rocky's PostgreSQL 16 stream. Downloaded five RPMs with DNF's
  `--downloadonly` option into `~/workspace/.assignment1-postgres-rpms`; all five
  signatures passed `rpmkeys --checksig`. Extracted them unprivileged using
  `rpm2cpio` and `cpio` into `~/workspace/.assignment1-postgres-runtime`.
  PostgreSQL is 16.15; it uses the VM's existing compatible operating-system
  libraries plus the extracted private libraries. No system database service
  was installed or enabled.
- Initialized `.assignment1-durable/.assignment1-postgres-data` with UTF-8,
  C.UTF-8 locale and data-page checksums. Kept fsync, synchronous_commit and
  full_page_writes enabled. The socket is `.assignment1-pg-socket`, mode 0700,
  port identifier 5433; `listen_addresses` is empty (no database TCP listener).
- Created database/role `assignment1`. The role has no superuser, database-creation
  or role-creation privileges. `pg_ident.conf` maps the lab's OS user to this role;
  `pg_hba.conf` permits peer authentication for that mapping and the OS cluster
  owner. No database password or public access was created.

`scripts/lab_start.py` resumes this provisioned setup: it restores/verifies the
hard mount, checks the existing cluster's private connection and durability,
then invokes the cloud launcher. It never initializes or resets a cluster. Its
Linux startup was verified on a replacement lab VM on 26 October 2026: the
existing workspace and database survived, the hard mount was restored, and the
private dashboard and scheduler started successfully. All 14 functional checks
passed again. Run `.venv/bin/python scripts/lab_start.py` in the remote terminal.
Restart and graceful shutdown were verified on 26 October 2026; the capture
record documents the separate lifecycle check and its host provenance.
Ctrl+C stops the owned assignment services before stopping a database it started;
an already-running database is left running. The hard mount must be restored on
each new lab VM session; no persistent system mount configuration was changed.

Once the database is ready, use Python 3.12 and the locked requirements in the
checkout's `.venv`, then run `python scripts/local.py --environment cloud
--startup-timeout 300`. The server binds to loopback and the scheduler runs every
two minutes. The launcher disables interactive prompts and distinguishes an
early process exit from an expired readiness deadline. Its default startup
budget is 180 seconds; it prints the URL only after a successful health check.

View http://127.0.0.1:4207 in the remote desktop's browser. Keep the portal/session
open during the demonstration and respect the lab's 15-minute inactivity limit.
This is session-bound cloud execution, not a continuously available hosted service.

Use `PREFECT_API_URL=http://127.0.0.1:4207/api .venv/bin/python -m src.verify
--wait-scheduled` in a second remote terminal after two automatic cycles. Export
the outputs and capture both the BITS lab identity/status and the remote browser
dashboard. A configured environment label alone does not establish hosting.

## Evidence boundaries

The execution environment in latest_run.json is a declared configuration value.
Neither that value nor a locally built image confirms remote hosting. The
verification manifest intentionally reports cloud verification as false because
it tests pipeline behavior, not the cloud provider's infrastructure.
