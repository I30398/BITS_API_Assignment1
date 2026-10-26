# BITS Prayogshala cloud evidence

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

## Frozen data and model evidence

The original VM's frozen evidence is retained in persistent `~/workspace` as
`CCZG506_Cloud_Evidence_20261026.zip` (5,817,999 bytes). Its snapshot contains
43 files, including hosting metadata, data outputs, model results, API details
and verification records. The archive was transferred on 26 October 2026 through
an isolated, SSH-signed temporary Git branch. Its SHA256 is
`00ca32c52f20044223366fc6eed0e7a5588e378113c52050d0f10fe8985365fc`.
The Mac verified the signature, archive checksum, ZIP CRC and every extracted
inventory hash. The temporary branch was then deleted; main history was not
rewritten, and the temporary GitHub CLI sign-in on the VM was removed.
The extracted files are now in this directory. The ZIP itself is not committed
to main. Original manifests and diagnostic logs are preserved unchanged.
The snapshots originate from different VM sessions and must retain their
individual capture times and host identities.

The original output set was captured on `ip-10-3-21-151` at
2026-10-25 20:54:12 UTC. Its verification records all 14 functional checks as
passing and five completed scheduled parent cycles. The verifier's default
`environment: local` and `cloud_deployment_verified: false` fields describe its
limited scope; they have not been changed to manufacture cloud proof. Hosting
is supported separately by the VM identity and provider/application captures.
Service logs include earlier troubleshooting as well as successful execution.

The reviewed cloud report is
[CCZG506_Assignment1_Review.docx](../../report/cloud-review/CCZG506_Assignment1_Review.docx).
The cloud confirmation setting is now true. The demonstration video URL remains
required before generating the final `15.docx`.

## Restart and graceful shutdown

The committed launcher was tested again on replacement host
`ip-10-3-21-143.ap-south-1.compute.internal` on 26 October 2026. Startup returned
HTTP 200 on the private dashboard; all 14 checks passed, with five fresh completed
scheduled parent cycles after restart. Some overdue scheduled runs drained after
resumption, so their actual start gaps are not evidence of a changed interval.
The deployment remained configured for 120 seconds and concurrency one.

After waiting for zero running/pending project flows, SIGINT was sent to the
owned launcher. The launcher exited, the dashboard stopped accepting connections,
and `pg_ctl status` confirmed the owned database was stopped. No tracked VM source
changes were present. The frozen archive's checksum remained unchanged.

[Cropped terminal result](lifecycle/08_lifecycle.png) records these observations.
[The review record](lifecycle/review_record.json) is explicitly transcribed from
that terminal output; the original machine-written result remains on the VM in
`~/workspace/.assignment1-lifecycle-20261026/result.json`. Its separate
[capture record](lifecycle/capture_inventory.json) documents the crop and hashes.
