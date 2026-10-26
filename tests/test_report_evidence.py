"""Prevent a cloud report from silently using altered frozen evidence."""
import json
import shutil

import pytest

from src import config
from src.generate_report import validate_snapshot


@pytest.fixture
def snapshot(tmp_path):
    source = config.PROJECT_ROOT / "evidence/cloud-prayogshala-20261026"
    target = tmp_path / "snapshot"
    shutil.copytree(source, target)
    return target


def test_frozen_inventory_and_separate_capture_provenance(snapshot):
    hosting, verification = validate_snapshot(snapshot)
    assert hosting["hostname"] != hosting["screenshot_host"]
    assert len(verification["scheduled_parent_runs"]) >= 2
    # Hosting review must not rewrite the original verifier's scope claim.
    assert verification["cloud_deployment_verified"] is False


def test_changed_model_results_are_rejected(snapshot):
    path = snapshot / "outputs/models/latest_metrics.json"
    results = json.loads(path.read_text())
    results["models"][0]["accuracy"] = 1.0
    path.write_text(json.dumps(results))
    with pytest.raises(ValueError, match="Snapshot checksum mismatch"):
        validate_snapshot(snapshot)


def test_changed_dashboard_capture_is_rejected(snapshot):
    (snapshot / "screenshots/01_dashboard.png").write_bytes(b"altered capture")
    with pytest.raises(ValueError, match="Screenshot checksum mismatch"):
        validate_snapshot(snapshot)


def test_inventory_cannot_read_outside_snapshot(snapshot):
    path = snapshot / "inventory.json"
    entries = json.loads(path.read_text())
    entries[0]["path"] = "../outside.txt"
    path.write_text(json.dumps(entries))
    with pytest.raises(ValueError, match="Invalid snapshot path"):
        validate_snapshot(snapshot)
