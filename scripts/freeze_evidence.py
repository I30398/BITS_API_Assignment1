"""Freeze a verified local review without copying environments or model binaries."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from filelock import FileLock
from src import config
from src.artifact_io import sha256_file, source_fingerprint, write_json
from src.verify import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/local-review")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("Choose a new --output folder; existing review evidence is never overwritten.")
    with FileLock(str(config.OUTPUTS_DIR / ".workflow.lock"), timeout=30):
        verify(wait_scheduled=True, timeout=0)
        files = [p for p in config.OUTPUTS_DIR.rglob("*") if p.is_file()
                 and "service_logs" not in p.parts
                 and p.suffix in [".json", ".jsonl", ".csv", ".png", ".txt"]]
        output.mkdir(parents=True)
        for path in files:
            destination = output / path.relative_to(config.OUTPUTS_DIR)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        report = ROOT / "report/current/CCZG506_Assignment1_Review.docx"
        if report.exists():
            shutil.copy2(report, output / report.name)
        runtime = {"python": platform.python_version(), "platform": platform.platform(),
                   "source_sha256": source_fingerprint(),
                   "requirements_lock_sha256": sha256_file(ROOT / "requirements-lock.txt"),
                   "packages": {name: importlib.metadata.version(name) for name in
                                ["prefect", "pandas", "numpy", "scikit-learn", "fastapi", "sqlalchemy"]}}
        write_json(runtime, output / "runtime.json")
        inventory = [{"path": str(p.relative_to(output)), "sha256": sha256_file(p)}
                     for p in sorted(output.rglob("*")) if p.is_file()]
        write_json({"environment": "local", "cloud_verified": False,
                    "source_sha256": source_fingerprint(), "files": inventory,
                    "model_binaries_included": False,
                    "note": "verification.json catalogues the original live output set; inventory.json covers files copied into this review."},
                   output / "inventory.json")
    print(output)


if __name__ == "__main__":
    main()
