"""Verify that lab restarts refuse unsafe database storage without resetting it."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("lab_start", Path(__file__).parents[1] / "scripts/lab_start.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class StorageChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.durable = self.work / ".assignment1-durable"
        self.data = self.durable / ".assignment1-postgres-data"
        self.data.mkdir(parents=True)
        (self.data / "PG_VERSION").write_text("16\n")
        self.original = dict(target=str(self.work), source="course:/workspace", fstype="nfs4", options="rw,soft")
        self.current = dict(target=str(self.durable), source="course:/workspace", fstype="nfs4", options="rw,hard,nosharecache")
        for name, value in (("WORK", self.work), ("DURABLE", self.durable), ("DATA", self.data)):
            item = patch.object(lab, name, value)
            item.start()
            self.addCleanup(item.stop)

    def test_existing_supported_cluster_is_preserved(self):
        marker = self.data / "existing-data"
        marker.write_text("retain this cluster")
        with patch.object(lab, "mount_info", side_effect=[self.original, self.current]), \
             patch.object(lab.subprocess, "run") as mutation:
            lab.prepare_storage()
            mutation.assert_not_called()
        self.assertEqual(marker.read_text(), "retain this cluster")

    def test_soft_database_mount_is_rejected(self):
        self.current["options"] = "rw,soft"
        with patch.object(lab, "mount_info", side_effect=[self.original, self.current]):
            with self.assertRaisesRegex(RuntimeError, "storage requirements"):
                lab.prepare_storage()

    def test_failed_mount_restore_does_not_initialize_database(self):
        with patch.object(lab, "mount_info", side_effect=[self.original, self.original]), \
             patch.object(lab.subprocess, "run", return_value=Mock(returncode=1)) as command:
            with self.assertRaisesRegex(RuntimeError, "startup was refused"):
                lab.prepare_storage()
            self.assertEqual(command.call_count, 1)
        self.assertEqual((self.data / "PG_VERSION").read_text(), "16\n")

    def test_unexpected_network_export_is_rejected(self):
        self.current["source"] = "other:/workspace"
        with patch.object(lab, "mount_info", side_effect=[self.original, self.current]):
            with self.assertRaisesRegex(RuntimeError, "storage requirements"):
                lab.prepare_storage()


if __name__ == "__main__":
    unittest.main()
