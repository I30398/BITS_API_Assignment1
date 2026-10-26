# BITS Prayogshala cloud screenshots

These images were captured from the running Prefect application and its BITS
hosting portal on 26 October 2026, after restarting the services on the
replacement VM `ip-10-3-17-92.ap-south-1.compute.internal`.

CleanShot X captured the Mac screen. The committed copies contain only the VM
application or provider-status viewport: the macOS interface and outer browser session address were
removed with a rectangular crop. No application content, metrics, logs or run
states were changed. Capture times, original-image hashes, crop coordinates and
committed-image hashes are recorded in
[capture_inventory.json](screenshots/capture_inventory.json).

| Image | Visible evidence |
| --- | --- |
| [Dashboard](screenshots/01_dashboard.png) | 106 completed flow runs, 488 completed tasks, and zero failed or crashed runs at capture time. Flow totals include parent and child flows. |
| [Run history](screenshots/02_flow_runs.png) | Completed automatic parent workflows and their DataOps/MLOps child runs, including parent starts at 05:17:39 and 05:19:33 IST. |
| [Deployment](screenshots/03_deployments.png) | One Ready deployment, with an Active schedule every two minutes. |
| [ML run](screenshots/05_ml_run_logs.png) | Completed seven-task ML pipeline, train/test split, Logistic Regression and Random Forest training, plots and activity logs. |
| [Data run](screenshots/06_data_run_logs.png) | Completed nine-task DataOps pipeline, ingestion, missing values, normalisation, EDA, persistence and activity logs. |
| [Hosting status](screenshots/07_hosting.png) | BITS API DRIVEN CLOUD NATIVE VIRTUAL - CCZG506 session Running, with the provider's persistence and inactivity limits. Connection credentials are excluded. |

The ML run `esoteric-starfish` and DataOps run `whispering-polecat` belong to
the same completed parent workflow, `formidable-magpie`, started at 05:21:37 IST.
The dashboard screenshot was captured earlier than those run-detail screenshots.
These are observations at their capture times, not an availability guarantee.
The lab is session-bound and is subject to its inactivity limits.

## Remaining evidence transfer

The original VM's frozen evidence is retained in persistent `~/workspace` as
`CCZG506_Cloud_Evidence_20261026.zip` (5,817,999 bytes). Its snapshot contains
43 files, including hosting metadata, data outputs, model results, API details
and verification records; its inventory hashes were checked after the VM was
replaced. That archive has **not yet been transferred into this checkout**.
The snapshots originate from different VM sessions and must retain their
individual capture times and host identities.

The cloud report and `cloud_evidence_confirmed` submission setting remain
pending until the archive is exported and its contents are reviewed together
with the screenshots. The demonstration video URL is also still required.
