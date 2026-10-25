"""
Sub-Objective 3 - API Access.

Uses Prefect's built-in REST API (via the Python client) to retrieve key
application details and display at least four of them:

  1. Flows registered in the application
  2. Deployments (with their schedules)
  3. Recent flow runs and their states
  4. Work pools / workers
  5. Aggregate run statistics

Prerequisite: a Prefect server must be reachable (either `prefect server start`
locally, or Prefect Cloud configured via PREFECT_API_URL / PREFECT_API_KEY).

Usage:  python -m src.api_access
Output: prints a report and writes outputs/api_details.json for the report doc.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from prefect.client.orchestration import get_client

from src import config
from src.artifact_io import atomic_path, write_json, source_fingerprint
from prefect.client.schemas.filters import FlowFilter, FlowFilterName


async def _gather() -> dict:
    details: dict = {"retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "source_sha256": source_fingerprint(),
                    "pipeline_version": config.PIPELINE_VERSION}
    project_filter = FlowFilter(name=FlowFilterName(any_=config.FLOW_NAMES))
    async with get_client() as client:
        # Detail 1 - Flows
        flows = await client.read_flows(flow_filter=project_filter)
        details["flows"] = [
            {"name": f.name, "id": str(f.id),
             "created": f.created.isoformat() if f.created else None}
            for f in flows
        ]

        # Detail 2 - Deployments + schedules
        deployments = await client.read_deployments(flow_filter=project_filter)
        dep_list = []
        for d in deployments:
            schedules = []
            for s in (d.schedules or []):
                sched = getattr(s, "schedule", None)
                interval = getattr(sched, "interval", None)
                schedules.append({
                    "active": s.active,
                    "interval_seconds": interval.total_seconds()
                    if interval else None,
                })
            dep_list.append({
                "name": d.name,
                "id": str(d.id),
                "paused": d.paused,
                "concurrency_limit": d.global_concurrency_limit.limit
                if d.global_concurrency_limit else None,
                "tags": d.tags,
                "schedules": schedules,
            })
        details["deployments"] = dep_list

        # Detail 3 - Recent flow runs + states (executed runs, newest first)
        from prefect.client.schemas.sorting import FlowRunSort
        from prefect.client.schemas.filters import (
            FlowRunFilter, FlowRunFilterState, FlowRunFilterStateType,
        )
        from prefect.client.schemas.objects import StateType
        executed_filter = FlowRunFilter(
            state=FlowRunFilterState(
                type=FlowRunFilterStateType(any_=[
                    StateType.COMPLETED, StateType.FAILED,
                    StateType.RUNNING, StateType.CRASHED,
                ])
            )
        )
        runs = await client.read_flow_runs(
            limit=20, flow_run_filter=executed_filter, flow_filter=project_filter,
            sort=FlowRunSort.START_TIME_DESC,
        )
        details["recent_flow_runs"] = [
            {"name": r.name,
             "state": r.state_name,
             "id": str(r.id),
             "flow_id": str(r.flow_id),
             "deployment_id": str(r.deployment_id) if r.deployment_id else None,
             "start_time": r.start_time.isoformat() if r.start_time else None,
             "total_run_time_s": r.total_run_time.total_seconds()
             if r.total_run_time else None}
            for r in runs
        ]

        # Detail 4 - Work pools
        try:
            pools = await client.read_work_pools()
            details["work_pools"] = [
                {"name": p.name, "type": p.type, "status": str(p.status)}
                for p in pools
            ]
        except Exception as exc:  # work pools optional in some setups
            details["work_pools"] = {"note": f"unavailable: {exc}"}

        # Detail 5 - Aggregate run statistics (derived)
        all_runs = await client.read_flow_runs(limit=200, flow_filter=project_filter)
        by_state: dict[str, int] = {}
        for r in all_runs:
            by_state[r.state_name or "Unknown"] = \
                by_state.get(r.state_name or "Unknown", 0) + 1
        details["run_statistics"] = {
            "scope": "Sample of up to 200 runs for this project's flows; includes subflows",
            "total_flow_runs_sampled": len(all_runs),
            "runs_by_state": by_state,
            "n_flows": len(details["flows"]),
            "n_deployments": len(details["deployments"]),
        }
    return details


def _print_report(d: dict) -> None:
    line = "=" * 70
    print(line)
    print("PREFECT BUILT-IN API - KEY APPLICATION DETAILS")
    print(f"Retrieved at: {d['retrieved_at']}")
    print(line)

    print(f"\n[1] FLOWS ({len(d['flows'])})")
    for f in d["flows"]:
        print(f"    - {f['name']}  (id={f['id'][:8]}...)")

    print(f"\n[2] DEPLOYMENTS ({len(d['deployments'])})")
    for dep in d["deployments"]:
        scheds = ", ".join(
            (f"every {int(s['interval_seconds'])}s" if s['interval_seconds'] else "non-interval schedule")
            + f"{' [active]' if s['active'] else ' [paused]'}"
            for s in dep["schedules"]) or "no schedule"
        print(f"    - {dep['name']}  | {scheds}  | tags={dep['tags']}")

    print(f"\n[3] RECENT FLOW RUNS ({len(d['recent_flow_runs'])})")
    for r in d["recent_flow_runs"][:10]:
        print(f"    - {r['name']:<28} state={r['state']:<12} "
              f"start={r['start_time']}")

    print(f"\n[4] WORK POOLS")
    wp = d["work_pools"]
    if isinstance(wp, list):
        if not wp:
            print("    No work pools: process-based serving is used.")
        for p in wp:
            print(f"    - {p['name']}  type={p['type']}  status={p['status']}")
    else:
        print(f"    {wp}")

    print(f"\n[5] RUN STATISTICS")
    stats = d["run_statistics"]
    print(f"    flows={stats['n_flows']}  deployments={stats['n_deployments']}"
          f"  runs_sampled={stats['total_flow_runs_sampled']}")
    print(f"    runs_by_state={stats['runs_by_state']}")
    print("\n" + line)


def main() -> None:
    config.ensure_dirs()
    details = asyncio.run(_gather())
    import io
    from contextlib import redirect_stdout
    console = io.StringIO()
    with redirect_stdout(console):
        _print_report(details)
    print(console.getvalue(), end="")
    out = config.OUTPUTS_DIR / "api_details.json"
    write_json(details, out)
    with atomic_path(config.OUTPUTS_DIR / "api_access_console.txt") as temp:
        temp.write_text(console.getvalue(), encoding="utf-8")
    print(f"Saved full API response to: {out}")


if __name__ == "__main__":
    main()
