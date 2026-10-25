"""Resume an already provisioned BITS lab database and private assignment services.

Requires the signed PostgreSQL runtime and initialized cluster described in
docs/DEPLOYMENT.md. Never initializes, resets or deletes an existing database.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
WORK = Path.home() / "workspace"
DURABLE = WORK / ".assignment1-durable"
RUNTIME = WORK / ".assignment1-postgres-runtime"
DATA = DURABLE / ".assignment1-postgres-data"
SOCKET = WORK / ".assignment1-pg-socket"


def mount_info(path):
    result = subprocess.run(["findmnt", "-J", "-T", str(path), "-o",
                             "TARGET,SOURCE,FSTYPE,OPTIONS"],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["filesystems"][0]


def prepare_storage():
    original = mount_info(WORK)
    if original["fstype"] != "nfs4" or Path(original["target"]) != WORK:
        raise RuntimeError("Expected this lab's NFS4 workspace; inspect the host before proceeding.")
    DURABLE.mkdir(exist_ok=True)
    current = mount_info(DURABLE)
    if Path(current["target"]) != DURABLE:
        # A separate cache preserves the original lab mount's behavior. Use the
        # database only through DURABLE, never through the original soft mount.
        result = subprocess.run(["sudo", "-n", "mount", "-t", "nfs4", "-o",
                                 "hard,nosharecache", original["source"], str(DURABLE)],
                                capture_output=True, text=True, timeout=35)
        if result.returncode:
            raise RuntimeError("Cannot restore the assignment's hard NFS mount; "
                               "database startup was refused.")
        current = mount_info(DURABLE)
    flags = set(current["options"].split(","))
    if (current["fstype"] != "nfs4" or current["source"] != original["source"]
            or "hard" not in flags or flags.intersection({"soft", "softerr"})):
        raise RuntimeError("The database mount does not meet PostgreSQL storage requirements.")
    if not (DATA / "PG_VERSION").is_file() or (DATA / "PG_VERSION").read_text().strip() != "16":
        raise RuntimeError("An initialized PostgreSQL 16 cluster is required; no data was changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run one cycle instead of the schedule.")
    args = parser.parse_args()
    if sys.platform != "linux" or ROOT.parent != WORK:
        parser.error("Run this only from the provisioned checkout directly inside ~/workspace.")
    prepare_storage()
    binaries = RUNTIME / "usr/bin"
    if not (binaries / "pg_ctl").is_file():
        raise RuntimeError("Persistent PostgreSQL binaries are missing; see deployment setup.")
    db_env = os.environ.copy()
    db_env["LD_LIBRARY_PATH"] = ":".join(str(RUNTIME / part) for part in
        ("usr/lib64", "usr/lib64/pgsql", "usr/lib64/pgsql/private"))
    SOCKET.mkdir(mode=0o700, exist_ok=True)
    SOCKET.chmod(0o700)
    control = [str(binaries / "pg_ctl"), "-D", str(DATA)]
    status = subprocess.run(control + ["status"], env=db_env, capture_output=True)
    if status.returncode not in (0, 3):
        raise RuntimeError("Cannot determine database status; inspect it before restarting.")
    owned = status.returncode == 3
    try:
        if owned:
            subprocess.run(control + ["-l", str(WORK / ".assignment1-postgres.log"),
                                      "-w", "-t", "90", "start"], env=db_env, check=True)
        # Check authentication, durability and absence of TCP listeners before
        # starting Prefect. The app role has no cluster administration privileges.
        result = subprocess.run([str(binaries / "psql"), "-h", str(SOCKET), "-p", "5433",
            "-U", "assignment1", "-d", "assignment1", "-v", "ON_ERROR_STOP=1", "-tAc",
            "SELECT current_user, current_setting('fsync'), "
            "current_setting('synchronous_commit'), current_setting('full_page_writes'), "
            "current_setting('listen_addresses');"], env=db_env, capture_output=True, text=True, check=True)
        if result.stdout.strip() != "assignment1|on|on|on|":
            raise RuntimeError("Database durability/private-listener checks failed; startup refused.")
        env = os.environ.copy()
        env["PREFECT_SERVER_DATABASE_CONNECTION_URL"] = (
            "postgresql+asyncpg://assignment1@/assignment1?" + urlencode({"host": str(SOCKET), "port": 5433}))
        command = [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/local.py"),
                   "--environment", "cloud", "--startup-timeout", "300"]
        if args.once:
            command.append("--once")
        with subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True) as services:
            try:
                return services.wait()
            except KeyboardInterrupt:
                services.send_signal(signal.SIGINT)
                try:
                    services.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    services.terminate()
                    services.wait(timeout=15)
                return 0
    finally:
        if owned:
            subprocess.run(control + ["-m", "fast", "-w", "-t", "90", "stop"],
                           env=db_env, check=True)


if __name__ == "__main__":
    sys.exit(main())
