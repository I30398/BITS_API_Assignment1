"""Start this assignment's private dashboard and scheduler, or run one cycle."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def filesystem_type(path, mountinfo=Path("/proc/self/mountinfo")):
    """Find the most specific Linux mount, including paths containing spaces."""
    if not mountinfo.exists():
        return None
    path = path.resolve()
    matches = []
    for line in mountinfo.read_text().splitlines():
        fields, separator, details = line.partition(" - ")
        if not separator:
            continue
        mount = Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields.split()[4]))
        if path == mount or mount in path.parents:
            matches.append((len(mount.parts), details.split()[0]))
    return max(matches, default=(0, None))[1]


def check_database_storage(env):
    connection = env.get("PREFECT_SERVER_DATABASE_CONNECTION_URL") or env.get("PREFECT_API_DATABASE_CONNECTION_URL", "")
    if connection and not connection.startswith("sqlite"):
        return
    if connection:
        prefix = "sqlite+aiosqlite:///"
        if not connection.startswith(prefix) or ":memory:" in connection:
            return
        database = Path(unquote(connection[len(prefix):].split("?", 1)[0]))
        if not database.is_absolute():
            database = ROOT / database
    else:
        database = Path(env["PREFECT_HOME"]) / "prefect.db"
    kind = filesystem_type(database)
    if kind in {"nfs", "nfs4", "cifs", "smb3"}:
        raise RuntimeError(f"SQLite WAL cannot use the {kind} database filesystem. "
                           "Configure PostgreSQL with PREFECT_SERVER_DATABASE_CONNECTION_URL "
                           "before starting this deployment.")


def healthy(url):
    try:
        with urllib.request.urlopen(url + "/api/health", timeout=2) as response:
            return response.status == 200
    except (OSError, TimeoutError):
        return False


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def wait_for_server(process, url, timeout):
    deadline = time.monotonic() + timeout
    while not healthy(url):
        status = process.poll()
        if status is not None:
            raise RuntimeError(f"Dashboard process exited with code {status}; check "
                               "outputs/current/service_logs/server.log")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Dashboard was not ready within {timeout:g} seconds; check "
                               "outputs/current/service_logs/server.log")
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run one complete cycle, then exit.")
    parser.add_argument("--environment", choices=["local", "cloud"], default="local",
                        help="Execution label; use cloud only when actually running on a cloud VM.")
    parser.add_argument("--startup-timeout", type=float, default=180,
                        help="Seconds allowed for server imports and database startup (default: 180).")
    args = parser.parse_args()
    if not 0 < args.startup_timeout < float("inf"):
        parser.error("--startup-timeout must be a finite positive number")
    python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    if not python.exists():
        raise SystemExit("Create .venv and install requirements-lock.txt first; see README.md.")
    url = "http://127.0.0.1:4207"
    env = os.environ.copy()
    env.update(PREFECT_HOME=str(ROOT / ".prefect"), PREFECT_API_URL=url + "/api",
               PREFECT_UI_API_URL=url + "/api", PREFECT_SERVER_ANALYTICS_ENABLED="false",
               DO_NOT_TRACK="1", PREFECT_CLI_PROMPT="false",
               MPLCONFIGDIR=str(ROOT / ".prefect/matplotlib"), ASSIGNMENT_ENVIRONMENT=args.environment)
    check_database_storage(env)
    logs = ROOT / "outputs/current/service_logs"
    logs.mkdir(parents=True, exist_ok=True)
    server = runner = None
    with (logs / "server.log").open("a", encoding="utf-8") as server_log, \
         (logs / "runner.log").open("a", encoding="utf-8") as runner_log:
        try:
            if not healthy(url):
                print(f"Starting dashboard; allowing {args.startup_timeout:g} seconds for readiness...", flush=True)
                server = subprocess.Popen([str(python), "-m", "prefect", "server", "start",
                    "--host", "127.0.0.1", "--port", "4207"], cwd=ROOT, env=env,
                    stdin=subprocess.DEVNULL, stdout=server_log, stderr=subprocess.STDOUT)
                wait_for_server(server, url, args.startup_timeout)
            print("Dashboard: " + url, flush=True)
            if args.once:
                result = subprocess.run([str(python), "-m", "src.workflow"], cwd=ROOT, env=env)
                return result.returncode
            runner = subprocess.Popen([str(python), "-m", "src.deploy"], cwd=ROOT, env=env,
                                      stdout=runner_log, stderr=subprocess.STDOUT)
            print("Automatic cycle every two minutes. Keep this window open; Ctrl+C stops owned services.", flush=True)
            while runner.poll() is None:
                if server and server.poll() is not None:
                    raise RuntimeError("The dashboard server stopped. Check its log.")
                time.sleep(0.5)
            return runner.returncode
        except KeyboardInterrupt:
            return 0
        finally:
            stop(runner)
            stop(server)


if __name__ == "__main__":
    sys.exit(main())
