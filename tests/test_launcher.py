"""Startup failure and network-storage regression checks; standard library only."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("assignment_launcher", Path(__file__).parents[1] / "scripts/local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherChecks(unittest.TestCase):
    def test_cold_start_can_exceed_original_sixty_seconds(self):
        with patch.object(launcher, "healthy", side_effect=[False, False, True]), \
             patch.object(launcher.time, "monotonic", side_effect=[0, 61, 90]), \
             patch.object(launcher.time, "sleep"):
            launcher.wait_for_server(Mock(poll=Mock(return_value=None)), "http://unused", 180)

    def test_crash_is_distinct_from_readiness_timeout(self):
        with patch.object(launcher, "healthy", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "exited with code 7"):
                launcher.wait_for_server(Mock(poll=Mock(return_value=7)), "http://unused", 180)

    def test_unhealthy_server_is_never_reported_ready(self):
        with patch.object(launcher, "healthy", return_value=False), \
             patch.object(launcher.time, "monotonic", side_effect=[0, 181]):
            with self.assertRaisesRegex(RuntimeError, "not ready within 180 seconds"):
                launcher.wait_for_server(Mock(poll=Mock(return_value=None)), "http://unused", 180)

    def test_most_specific_mount_and_escaped_space(self):
        with tempfile.TemporaryDirectory(prefix="assignment mount ") as folder:
            mount = Path(folder).resolve()
            info = mount / "mountinfo"
            escaped = str(mount).replace(" ", r"\040")
            info.write_text(f"1 0 8:0 / / rw - ext4 /dev/root rw\n2 1 0:9 / {escaped} rw - nfs4 server:/course rw\n")
            self.assertEqual(launcher.filesystem_type(mount / "future/prefect.db", info), "nfs4")
            self.assertEqual(launcher.filesystem_type(Path("/outside"), info), "ext4")

    def test_nfs_sqlite_rejected_before_launch(self):
        with patch.object(launcher, "filesystem_type", return_value="nfs4"):
            with self.assertRaisesRegex(RuntimeError, "Configure PostgreSQL"):
                launcher.check_database_storage({"PREFECT_HOME": "/course/.prefect"})

    def test_postgresql_does_not_use_sqlite_storage_check(self):
        with patch.object(launcher, "filesystem_type") as lookup:
            launcher.check_database_storage({"PREFECT_SERVER_DATABASE_CONNECTION_URL": "postgresql+asyncpg://localhost/course"})
            lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
