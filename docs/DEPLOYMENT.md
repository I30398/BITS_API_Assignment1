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

## Evidence boundaries

The execution environment in latest_run.json is a declared configuration value.
Neither that value nor a locally built image confirms remote hosting. The
verification manifest intentionally reports cloud verification as false because
it tests pipeline behavior, not the cloud provider's infrastructure.
