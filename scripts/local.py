"""Start this assignment's local dashboard and scheduler, or run one cycle."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run one complete cycle, then exit.")
    args = parser.parse_args()
    python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    if not python.exists():
        raise SystemExit("Create .venv and install requirements-lock.txt first; see README.md.")
    url = "http://127.0.0.1:4207"
    env = os.environ.copy()
    env.update(PREFECT_HOME=str(ROOT / ".prefect"), PREFECT_API_URL=url + "/api",
               PREFECT_UI_API_URL=url + "/api", PREFECT_SERVER_ANALYTICS_ENABLED="false",
               MPLCONFIGDIR=str(ROOT / ".prefect/matplotlib"), ASSIGNMENT_ENVIRONMENT="local")
    logs = ROOT / "outputs/current/service_logs"
    logs.mkdir(parents=True, exist_ok=True)
    server = runner = None
    with (logs / "server.log").open("a", encoding="utf-8") as server_log, \
         (logs / "runner.log").open("a", encoding="utf-8") as runner_log:
        try:
            if not healthy(url):
                server = subprocess.Popen([str(python), "-m", "prefect", "server", "start",
                    "--host", "127.0.0.1", "--port", "4207"], cwd=ROOT, env=env,
                    stdout=server_log, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 60
                while not healthy(url):
                    if server.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Dashboard startup failed; check outputs/current/service_logs/server.log")
                    time.sleep(0.5)
            print("Dashboard: " + url, flush=True)
            if args.once:
                result = subprocess.run([str(python), "-m", "src.workflow"], cwd=ROOT, env=env)
                return result.returncode
            runner = subprocess.Popen([str(python), "-m", "src.deploy"], cwd=ROOT, env=env,
                                      stdout=runner_log, stderr=subprocess.STDOUT)
            print("Automatic cycle every two minutes. Keep this window open; Ctrl+C stops owned services.", flush=True)
            while runner.poll() is None:
                if server and server.poll() is not None:
                    raise RuntimeError("The local server stopped. Check its log.")
                time.sleep(0.5)
            return runner.returncode
        except KeyboardInterrupt:
            return 0
        finally:
            stop(runner)
            stop(server)


if __name__ == "__main__":
    sys.exit(main())
