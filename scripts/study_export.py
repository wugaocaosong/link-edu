"""Research-safe JSON/CSV helpers for coordinator exports.

This tool exports only the data explicitly supplied to it; it does not query
ordinary classroom tables or infer research assignments from demo accounts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from services.study_exports import (  # noqa: E402
    aggregate_raters,
    blank_rating,
    build_coordinator_export,
    build_sealed_input,
    make_participant_delivery,
    ratings_csv,
    seal_packet,
    validate_blind_clip,
)


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_blind(args):
    clip = validate_blind_clip(read_json(args.input))
    destination = Path(args.out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for rater in ("R1", "R2"):
        record = blank_rating(clip, rater)
        # These files intentionally contain no group, participant, phase, date, or source filename.
        write_json(destination / f"blind_{clip['clip_id']}_{rater}.json", record)
        (destination / f"blind_{clip['clip_id']}_{rater}.csv").write_text(
            ratings_csv([record]), encoding="utf-8-sig", newline="")


def export_aggregate(args):
    payload = read_json(args.input)
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("input must be a list of independently submitted rater forms")
    results = aggregate_raters(records)
    output = Path(args.out)
    report = {"sample_type": payload["sample_type"], "rubric_version": payload.get("rubric_version"),
              "results": results} if isinstance(payload, dict) and payload.get("sample_type") else results
    write_json(output, report)
    csv_path = output.with_suffix(".csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["clip_id", "status", "R1_total", "R2_total", "coordinator_mean_total"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        import csv
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow({"clip_id": row["clip_id"], "status": row["status"],
                "R1_total": row["rater_totals"]["R1"], "R2_total": row["rater_totals"]["R2"],
                "coordinator_mean_total": row["coordinator_mean_total"]})


def seal(args):
    events = read_json(args.input)
    if not isinstance(events, list):
        raise ValueError("input must be a JSON array of classroom events")
    motion = read_json(args.motion) if args.motion else None
    packet = seal_packet(args.group, args.session_id, events, model=args.model,
        rubric_version=args.rubric, template_version=args.template, motion_summary=motion)
    write_json(Path(args.out), packet)


def issue_report(args):
    payload = read_json(args.input)
    if not isinstance(payload, dict):
        raise ValueError("issue payload must be a JSON object")
    delivered = make_participant_delivery(
        events=payload.get("events"),
        evidence_selections=payload.get("evidence_selections"),
        self_review=payload.get("self_review"),
        report_text=payload.get("report_text"),
        issued_at=payload.get("issued_at"),
        input_sha256=payload.get("input_sha256"),
        model=payload.get("model"),
        rubric_version=payload.get("rubric_version"),
        template_version=payload.get("template_version"),
    )
    write_json(Path(args.out), delivered)


def generate_report(args):
    from dotenv import load_dotenv
    from services.study_export_review import generate_study_review
    load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env")
    packet, events = read_json(args.packet), read_json(args.events)
    report = generate_study_review(packet, events, api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "60")))
    write_json(Path(args.out), report)


def coordinator_export(args):
    payload = read_json(args.input)
    if not isinstance(payload, dict):
        raise ValueError("coordinator input must be a JSON object")
    output = build_coordinator_export(payload.get("study_metadata"), payload.get("rounds"))
    write_json(Path(args.out), output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    blind = commands.add_parser("blind", help="create two separate anonymous rater forms")
    blind.add_argument("--input", required=True, help="one clip JSON with two opportunity rows")
    blind.add_argument("--out-dir", required=True)
    blind.set_defaults(func=export_blind)
    aggregate = commands.add_parser("aggregate", help="calculate two-rater coordinator summary")
    aggregate.add_argument("--input", required=True, help="JSON list of independently submitted rater forms")
    aggregate.add_argument("--out", required=True)
    aggregate.set_defaults(func=export_aggregate)
    seal_cmd = commands.add_parser("seal-input", help="build frozen, hashed model input packet")
    seal_cmd.add_argument("--input", required=True, help="JSON event array")
    seal_cmd.add_argument("--group", choices=("transcript", "multimodal"), required=True)
    seal_cmd.add_argument("--session-id", required=True)
    seal_cmd.add_argument("--model", required=True)
    seal_cmd.add_argument("--rubric", required=True)
    seal_cmd.add_argument("--template", required=True)
    seal_cmd.add_argument("--motion", help="reviewed motion-summary JSON array; multimodal only")
    seal_cmd.add_argument("--out", required=True)
    seal_cmd.set_defaults(func=seal)
    issue_cmd = commands.add_parser("issue-report", help="archive an exact report after saved self-review and evidence checks")
    issue_cmd.add_argument("--input", required=True, help="JSON with events, selected sequences, self-review, exact report and frozen versions")
    issue_cmd.add_argument("--out", required=True, help="write directly inside the approved research storage")
    issue_cmd.set_defaults(func=issue_report)
    generate_cmd = commands.add_parser("generate-report", help="generate a frozen formative report draft; does not issue it")
    generate_cmd.add_argument("--packet", required=True, help="sealed packet JSON; only its input object is sent")
    generate_cmd.add_argument("--events", required=True, help="source event JSON for quote and playback verification")
    generate_cmd.add_argument("--out", required=True, help="draft JSON path in approved research storage")
    generate_cmd.set_defaults(func=generate_report)
    coordinator = commands.add_parser("coordinator", help="build coordinator-only two-round research export")
    coordinator.add_argument("--input", required=True, help="coordinator metadata and two round event arrays")
    coordinator.add_argument("--out", required=True, help="write only to approved research storage")
    coordinator.set_defaults(func=coordinator_export)
    args = parser.parse_args()
    try:
        args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
