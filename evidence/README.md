# Reviewed execution evidence

The two subfolders record local execution of the revised Assignment I code on
25 October 2026. See docs/VALIDATION.md for scope and limitations.

- local-review: frozen macOS results, report, actual dashboard screenshots and
  per-file inventory. All copied inventory hashes were verified.
- docker-review: Linux container runtime, independent model metrics and passing
  scheduled-run checks. This is a local Docker test, not a cloud deployment.

Original repository outputs are historical baseline evidence and were preserved.
New captures include development failures as well as subsequent successes.
Current-source validation is identified by the source fingerprint and completed
scheduled parent run IDs, not by hiding earlier failures.
