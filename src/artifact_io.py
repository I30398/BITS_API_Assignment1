"""Publish complete files and serialize append operations across processes."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile

from filelock import FileLock


@contextmanager
def atomic_path(destination: Path):
    """Readers see the previous complete file or the new complete file."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{destination.stem}-",
                                suffix=destination.suffix, dir=destination.parent)
    os.close(fd)
    temp = Path(name)
    try:
        yield temp
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def write_csv(frame, destination: Path, **kwargs):
    with atomic_path(destination) as temp:
        frame.to_csv(temp, **kwargs)


def write_json(value, destination: Path):
    with atomic_path(destination) as temp:
        temp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def append_record(destination: Path, record: dict):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(destination) + ".lock", timeout=30):
        with destination.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_fingerprint() -> str:
    """Fingerprint runtime/API code; report-only layout changes do not retrain ML."""
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        if path.name == "generate_report.py":
            continue
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
