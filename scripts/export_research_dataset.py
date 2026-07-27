#!/usr/bin/env python3
"""Export a research-oriented dataset from the campus simulation database."""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection, using_postgres  # noqa: E402
from app.schema import RESEARCH_SYSTEM_SQL  # noqa: E402

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "exports" / "research"

DATASETS = {
    "agents": "residents",
    "agent_profiles": "agent_profiles",
    "memories": "memories",
    "simulation_actions": "simulation_action_logs",
    "relationships": "relationships",
    "relationship_dynamics": "relationship_dynamics",
    "campus_state": "campus_state",
    "campus_spaces": "campus_spaces",
    "world_ticks": "world_ticks",
    "events": "world_event_stream",
    "observer_records": "observer_sessions",
    "model_calls": "model_call_logs",
    "action_plans": "agent_action_plans",
    "participant_actions": "participant_actions",
    "experiment_runs": "experiment_runs",
    "world_snapshots": "world_snapshots",
}


def row_to_dict(row):
    return dict(row) if row is not None else {}


def safe_json(text, fallback):
    if not text:
        return fallback
    try:
        return json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return fallback


def table_columns(conn, table_name):
    try:
        return [row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    except Exception:
        return []


def table_exists(conn, table_name):
    return bool(table_columns(conn, table_name))


def fetch_table(conn, table_name, order_by=None):
    if not table_exists(conn, table_name):
        return []
    columns = table_columns(conn, table_name)
    order = order_by or ("id" if "id" in columns else columns[0])
    return [row_to_dict(row) for row in conn.execute(f"SELECT * FROM {table_name} ORDER BY {order}").fetchall()]


def filter_by_day(rows, from_day=None, to_day=None):
    filtered = []
    for row in rows:
        day = row.get("day")
        if day is None:
            filtered.append(row)
            continue
        try:
            day_value = int(day)
        except (TypeError, ValueError):
            filtered.append(row)
            continue
        if from_day is not None and day_value < from_day:
            continue
        if to_day is not None and day_value > to_day:
            continue
        filtered.append(row)
    return filtered


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path, rows):
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_dataset(output_dir, name, rows, output_format):
    if output_format in {"json", "both"}:
        write_json(output_dir / f"{name}.json", rows)
    if output_format in {"csv", "both"}:
        write_csv(output_dir / f"{name}.csv", rows)


def summarize_agent_days(actions, memories, model_calls):
    summary = defaultdict(lambda: {
        "action_count": 0,
        "movement_count": 0,
        "social_action_count": 0,
        "memory_count": 0,
        "llm_calls": 0,
        "unique_spaces_visited": set(),
    })
    for row in actions:
        key = (row.get("resident_id"), row.get("day"))
        item = summary[key]
        item["resident_id"], item["day"] = key
        item["action_count"] += 1
        decision = safe_json(row.get("decision"), {})
        execution = safe_json(row.get("execution"), {})
        action = str(decision.get("action") or execution.get("action") or "")
        if action == "move":
            item["movement_count"] += 1
        if action in {"chat", "collaborate", "compete"}:
            item["social_action_count"] += 1
        location = execution.get("location") or decision.get("target_location")
        if location:
            item["unique_spaces_visited"].add(str(location))

    for row in memories:
        key = (row.get("resident_id"), row.get("day"))
        item = summary[key]
        item["resident_id"], item["day"] = key
        item["memory_count"] += 1

    for row in model_calls:
        resident_id = row.get("resident_id")
        if resident_id is None:
            continue
        created_at = str(row.get("created_at") or "")[:10]
        key = (resident_id, created_at)
        item = summary[key]
        item["resident_id"], item["day"] = created_at
        item["llm_calls"] += 1

    rows = []
    for item in summary.values():
        item = dict(item)
        item["unique_spaces_visited"] = len(item["unique_spaces_visited"])
        rows.append(item)
    return sorted(rows, key=lambda item: (str(item.get("day")), int(item.get("resident_id") or 0)))


def summarize_space_time(events, campus_state):
    rows = []
    for state in campus_state:
        rows.append({
            "source": "campus_state",
            "day": state.get("day"),
            "world_time": state.get("real_time") or state.get("created_at"),
            "location": "campus",
            "weather": state.get("weather"),
            "campus_mood": state.get("campus_mood"),
            "campus_flow": state.get("campus_flow"),
            "classroom_crowd": state.get("classroom_crowd"),
            "canteen_crowd": state.get("canteen_crowd"),
            "library_crowd": state.get("library_crowd"),
            "dorm_crowd": state.get("dorm_crowd"),
            "playground_crowd": state.get("playground_crowd"),
            "commercial_crowd": state.get("commercial_crowd"),
        })
    event_counts = Counter((event.get("day"), event.get("location") or "unknown") for event in events)
    for (day, location), count in event_counts.items():
        rows.append({
            "source": "world_event_stream",
            "day": day,
            "world_time": "",
            "location": location,
            "event_count": count,
        })
    return rows


def build_quality_report(datasets):
    residents = {row.get("id") for row in datasets.get("agents", [])}
    memories = datasets.get("memories", [])
    events = datasets.get("events", [])
    ticks = datasets.get("world_ticks", [])
    model_calls = datasets.get("model_calls", [])

    memory_keys = Counter(
        (row.get("resident_id"), row.get("day"), row.get("content"), row.get("source"))
        for row in memories
    )
    duplicate_memories = sum(count - 1 for count in memory_keys.values() if count > 1)
    orphan_events = [
        row.get("id") for row in events
        if row.get("resident_id") is not None and row.get("resident_id") not in residents
    ]
    running_ticks = [row.get("id") for row in ticks if row.get("status") == "running"]
    missing_related_events = [
        row.get("id") for row in model_calls
        if row.get("trigger_type") in {"observer", "admin"} and not row.get("related_event_id")
    ]

    checks = [
        {
            "name": "duplicate_memories",
            "status": "pass" if duplicate_memories == 0 else "warn",
            "count": duplicate_memories,
            "message": "Exact duplicate memories should be reviewed before analysis.",
        },
        {
            "name": "orphan_world_events",
            "status": "pass" if not orphan_events else "fail",
            "count": len(orphan_events),
            "sample_ids": orphan_events[:20],
        },
        {
            "name": "unfinished_world_ticks",
            "status": "pass" if not running_ticks else "warn",
            "count": len(running_ticks),
            "sample_ids": running_ticks[:20],
        },
        {
            "name": "model_calls_without_related_event",
            "status": "pass" if not missing_related_events else "warn",
            "count": len(missing_related_events),
            "sample_ids": missing_related_events[:20],
        },
        {
            "name": "legacy_run_id_links",
            "status": "warn",
            "message": "Most legacy operational tables do not yet contain run_id; export metadata records the selected run boundary.",
        },
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": "postgres" if using_postgres() else "sqlite",
        "row_counts": {name: len(rows) for name, rows in datasets.items()},
        "checks": checks,
    }


def create_export_job(conn, run_id, output_format, output_dir):
    cursor = conn.execute(
        """
        INSERT INTO research_export_jobs
        (run_id, export_format, export_path, status, metadata_json)
        VALUES (?, ?, ?, 'running', ?)
        """,
        (
            run_id,
            output_format,
            str(output_dir),
            json.dumps({"started_by": "scripts/export_research_dataset.py"}, ensure_ascii=False),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def finish_export_job(conn, job_id, quality_report, status="completed"):
    conn.execute(
        """
        UPDATE research_export_jobs
        SET status = ?, completed_at = CURRENT_TIMESTAMP, quality_report_json = ?
        WHERE id = ?
        """,
        (status, json.dumps(quality_report, ensure_ascii=False), job_id),
    )
    conn.commit()


def export_dataset(args):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = args.run_id or f"ad-hoc-{timestamp}"
    output_dir = Path(args.output_dir or DEFAULT_OUTPUT_DIR) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(RESEARCH_SYSTEM_SQL)
        job_id = create_export_job(conn, run_id, args.format, output_dir)
        datasets = {}
        try:
            for dataset_name, table_name in DATASETS.items():
                rows = fetch_table(conn, table_name)
                datasets[dataset_name] = filter_by_day(rows, args.from_day, args.to_day)

            if args.after_event_id:
                datasets["events"] = [
                    row for row in datasets["events"]
                    if int(row.get("id") or 0) > args.after_event_id
                ]

            datasets["agent_day"] = summarize_agent_days(
                datasets["simulation_actions"],
                datasets["memories"],
                datasets["model_calls"],
            )
            datasets["space_time"] = summarize_space_time(datasets["events"], datasets["campus_state"])
            quality_report = build_quality_report(datasets)
            metadata = {
                "run_id": run_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "format": args.format,
                "filters": {
                    "from_day": args.from_day,
                    "to_day": args.to_day,
                    "after_event_id": args.after_event_id,
                },
                "datasets": sorted(datasets.keys()),
            }
            for name, rows in datasets.items():
                write_dataset(output_dir, name, rows, args.format)
            write_json(output_dir / "experiment_metadata.json", metadata)
            write_json(output_dir / "data_quality_report.json", quality_report)
            finish_export_job(conn, job_id, quality_report)
        except Exception:
            finish_export_job(conn, job_id, {"error": "export failed"}, status="failed")
            raise

    return output_dir


def parse_args():
    parser = argparse.ArgumentParser(description="Export research datasets from the campus simulation database.")
    parser.add_argument("--run-id", default="", help="Research run id to write into export metadata.")
    parser.add_argument("--output-dir", default="", help="Base output directory. Defaults to exports/research.")
    parser.add_argument("--format", choices=["csv", "json", "both"], default="both")
    parser.add_argument("--from-day", type=int, default=None)
    parser.add_argument("--to-day", type=int, default=None)
    parser.add_argument("--after-event-id", type=int, default=0)
    return parser.parse_args()


def main():
    output_dir = export_dataset(parse_args())
    print(f"Research dataset exported to {output_dir}")


if __name__ == "__main__":
    main()
