"""Research-safe exports for the 《认识几分之一》 microteaching study.

This module deliberately keeps research exports separate from ordinary LINK
classroom reports. It contains no database writes and never assigns a missing
rating a numeric value.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from typing import Any

DIMENSIONS = (
    "概念指向",
    "理解诊断",
    "追问承接",
    "解释调整",
)
FROZEN_MODEL = "deepseek-v4-flash"
FROZEN_RUBRIC = "fraction-formative-1"
FROZEN_TEMPLATE = "fraction-narrative-1"
FROZEN_GENERATION = {"temperature": 0, "top_p": 1, "thinking": False, "max_tokens": 1200, "response_format": "json"}
OPPORTUNITY_COUNT = 2
BLIND_ID = re.compile(r"^[A-Z0-9]{6,16}$")
BLIND_SEMANTIC_TOKEN = re.compile(r"(?:^P\d|PRE|POST|BASE|FOLLOW|MULTI|TRANS|GROUP|TREAT|CTRL)")
BLIND_VISIBLE_MARKER = re.compile(r"(?:\bP\d{2}\b|(?:19|20)\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}|前测|后测|转写组|多模态组|实验组|对照组)")
MISSING_REASONS = {
    "opportunity_not_provided": "主持人未提供该回应机会",
    "speech_unintelligible": "关键发言听不清",
    "video_unreadable": "画面不可辨认",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _completed_reply_ids(events: list[dict]) -> set[str]:
    completed = {
        str((e.get("data") or {}).get("reply_id"))
        for e in events
        if e.get("type") == "playback"
        and (e.get("data") or {}).get("status") == "playback_completed"
        and (e.get("data") or {}).get("reply_id") not in (None, "")
    }
    incomplete = {
        str((e.get("data") or {}).get("reply_id"))
        for e in events
        if e.get("type") == "interrupt"
        or (e.get("type") == "playback" and (e.get("data") or {}).get("status") in {
            "playback_failed", "playback_cancelled", "cancelled",
        })
    }
    return completed - incomplete


def build_sealed_input(group: str, events: list[dict], motion_summary: list[dict] | None = None) -> dict:
    """Create the exact model-visible input; identity/group metadata stays outside it.

    Both groups receive byte-for-byte equivalent finalized transcript turns.
    Student turns are included only when there is an unambiguous completion
    receipt. The transcript condition receives no playback time or motion data.
    """
    if group not in {"transcript", "multimodal"}:
        raise ValueError("group must be transcript or multimodal")
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    completed = _completed_reply_ids(events)
    turns = []
    for event in sorted(events, key=lambda e: (int(e.get("id") or 0))):
        kind, data = event.get("type"), event.get("data") or {}
        if kind not in {"transcript", "student"} or not isinstance(data.get("text"), str):
            continue
        if kind == "student" and str(data.get("reply_id") or "") not in completed:
            continue
        event_id = event.get("id")
        turns.append({
            "turn_id": str(event_id) if event_id is not None else str(len(turns) + 1),
            "speaker": "teacher" if kind == "transcript" else "student",
            "text": data["text"],
        })
    result = {"transcript": turns}
    if group == "multimodal":
        reply_ids = {str((e.get("data") or {}).get("reply_id")) for e in events if e.get("type") == "student"}
        playback = []
        for event in events:
            data = event.get("data") or {}
            rid = str(data.get("reply_id") or "")
            if event.get("type") == "playback" and rid in reply_ids and type(event.get("at_ms")) is int:
                playback.append({"reply_id": rid, "status": data.get("status"), "at_ms": event["at_ms"]})
        result["playback"] = sorted(playback, key=lambda x: x["at_ms"])
        # Whitelist source-derived fields; callers must pass already reviewed summaries.
        safe_motion = []
        for item in motion_summary or []:
            if not isinstance(item, dict):
                continue
            safe = {k: item[k] for k in ("event_id", "at_ms", "modality", "observation") if k in item}
            if safe:
                safe_motion.append(safe)
        result["teacher_motion"] = safe_motion
    return result


def seal_packet(group: str, session_id: str, events: list[dict], *, model: str,
                rubric_version: str, template_version: str,
                motion_summary: list[dict] | None = None) -> dict:
    """Return a metadata envelope and a separately hash-sealed model input."""
    if not all(isinstance(v, str) and v.strip() for v in (session_id, model, rubric_version, template_version)):
        raise ValueError("session and frozen version fields are required")
    if (model, rubric_version, template_version) != (FROZEN_MODEL, FROZEN_RUBRIC, FROZEN_TEMPLATE):
        raise ValueError("model, rubric, and template must match the frozen study specification")
    model_input = build_sealed_input(group, events, motion_summary)
    return {
        "session_id": session_id,
        "group": group,
        "model": model,
        "rubric_version": rubric_version,
        "template_version": template_version,
        "generation": dict(FROZEN_GENERATION),
        "input_sha256": sha256_json(model_input),
        "input": model_input,
        "model_input_boundary": "Only the input object may be sent to the model.",
    }


def build_feedback_evidence(events: list[dict], selections: list[dict]) -> list[dict]:
    """Validate one or two participant-facing quote/action chains against source events."""
    if not isinstance(selections, list) or not 1 <= len(selections) <= 2:
        raise ValueError("participant feedback must select one or two verifiable sequences")
    by_id = {e.get("id"): e for e in events if type(e.get("id")) is int}
    completed = _completed_reply_ids(events)
    result = []
    for item in selections:
        student = by_id.get(item.get("student_event_id"))
        teacher = by_id.get(item.get("teacher_event_id"))
        if not student or student.get("type") != "student":
            raise ValueError("student quote must cite an actual student response event")
        reply_id = str((student.get("data") or {}).get("reply_id") or "")
        if reply_id not in completed:
            raise ValueError("student response is not verified as fully played; it cannot be reported as heard")
        completion_ids = [e["id"] for e in events if e.get("type") == "playback"
                          and str((e.get("data") or {}).get("reply_id") or "") == reply_id
                          and (e.get("data") or {}).get("status") == "playback_completed"
                          and type(e.get("id")) is int]
        next_teacher = min((e["id"] for e in events if e.get("type") == "transcript"
                            and type(e.get("id")) is int and completion_ids
                            and e["id"] > min(completion_ids)), default=None)
        if (not teacher or teacher.get("type") != "transcript" or not completion_ids
                or teacher["id"] != next_teacher):
            raise ValueError("teacher action must cite a later finalized teacher transcript event")
        student_text = (student.get("data") or {}).get("text")
        teacher_text = (teacher.get("data") or {}).get("text")
        if not isinstance(student_text, str) or not student_text.strip() or not isinstance(teacher_text, str) or not teacher_text.strip():
            raise ValueError("source turns must contain finalized non-empty text")
        classification = item.get("student_claim_type")
        if classification not in {"conclusion_only", "has_reason", "ambiguous"}:
            raise ValueError("classify only the actually played student words as conclusion, reason, or ambiguous")
        follow_up = str(item.get("what_response_did") or "").strip()
        next_step = str(item.get("next_step") or "").strip()
        if not follow_up or not next_step:
            raise ValueError("evidence interpretation and a specific next step are required")
        result.append({
            "student": {"event_id": student["id"], "reply_id": reply_id, "quote": student_text,
                        "claim_type": classification, "playback_status": "playback_completed"},
            "teacher": {"event_id": teacher["id"], "quote": teacher_text},
            "what_response_did": follow_up,
            "next_step": next_step,
            "next_step_source": "AI suggestion; not the participant's own revision goal",
        })
    return result


def make_participant_delivery(*, events: list[dict], evidence_selections: list[dict],
                              self_review: dict, report_text: str, issued_at: str,
                              input_sha256: str, model: str, rubric_version: str,
                              template_version: str) -> dict:
    """Record the immutable report text only after an independently saved self-review."""
    if not isinstance(self_review, dict) or not str(self_review.get("text") or "").strip():
        raise ValueError("independent self-review must be saved before issuing the report")
    if not self_review.get("saved_at"):
        raise ValueError("self-review timestamp is required")
    if not isinstance(report_text, str) or not 280 <= len(report_text.strip()) <= 900:
        raise ValueError("exact participant report must be 280-900 characters")
    if not re.fullmatch(r"[0-9a-f]{64}", str(input_sha256)):
        raise ValueError("input SHA-256 is required")
    if not all(isinstance(v, str) and v.strip() for v in (issued_at, model, rubric_version, template_version)):
        raise ValueError("issue timestamp and frozen versions are required")
    if (model, rubric_version, template_version) != (FROZEN_MODEL, FROZEN_RUBRIC, FROZEN_TEMPLATE):
        raise ValueError("report must use the frozen model, rubric, and template")
    evidence = build_feedback_evidence(events, evidence_selections)
    for sequence in evidence:
        for excerpt in (sequence["student"]["quote"], sequence["teacher"]["quote"],
                        sequence["what_response_did"], sequence["next_step"]):
            if excerpt not in report_text:
                raise ValueError("exact cited quotes, response interpretation, and next-step suggestion must appear in the delivered report")
    return {
        "self_review": {"text": self_review["text"], "saved_at": self_review["saved_at"]},
        "report_text": report_text,
        "issued_at": issued_at,
        "input_sha256": input_sha256,
        "model": model,
        "rubric_version": rubric_version,
        "template_version": template_version,
        "evidence_sequences": evidence,
    }


def classify_cross_round_followup(*, opportunity_status: str, teacher_response_observed: bool | None = None,
                                  evidence_sufficient: bool = True) -> str:
    """Keep absence, skipped response, and insufficient evidence distinct."""
    if not evidence_sufficient:
        return "cannot_assess"
    if opportunity_status == "not_provided":
        return "no_opportunity"
    if opportunity_status != "provided":
        raise ValueError("opportunity_status must be provided or not_provided")
    if teacher_response_observed is False:
        return "opportunity_provided_teacher_skipped"
    if teacher_response_observed is True:
        return "teacher_response_observed"
    return "cannot_assess"


def validate_blind_clip(clip: dict) -> dict:
    """Whitelist anonymous, video-verifiable data for one blind clip."""
    clip_id = clip.get("clip_id")
    if (not isinstance(clip_id, str) or not BLIND_ID.fullmatch(clip_id)
            or BLIND_SEMANTIC_TOKEN.search(clip_id)):
        raise ValueError("clip_id must be an opaque 6-16 character uppercase alphanumeric ID")
    opportunities = clip.get("opportunities")
    if not isinstance(opportunities, list) or len(opportunities) != OPPORTUNITY_COUNT:
        raise ValueError("blind clip must contain exactly two opportunity rows")
    clean = {"clip_id": clip_id, "opportunities": []}
    for expected, row in enumerate(opportunities, 1):
        if not isinstance(row, dict) or row.get("opportunity_no") != expected:
            raise ValueError("opportunities must be numbered 1 and 2 in video order")
        status = row.get("status", "present")
        if status not in {"present", *MISSING_REASONS.keys()}:
            raise ValueError("unsupported opportunity status")
        timecode = row.get("start_timecode")
        if timecode is not None and (not isinstance(timecode, str) or not re.fullmatch(r"\d{1,2}:\d{2}", timecode)):
            raise ValueError("start_timecode must be M:SS or null")
        item = {
            "opportunity_no": expected,
            "start_timecode": timecode,
            "status": status,
            "student_quote": str(row.get("student_quote") or "") if status == "present" else "",
            "teacher_action_quote_or_description": str(row.get("teacher_action_quote_or_description") or "") if status == "present" else "",
            "teacher_timecode": row.get("teacher_timecode") if status == "present" else None,
        }
        for field in ("student_quote", "teacher_action_quote_or_description"):
            if BLIND_VISIBLE_MARKER.search(item[field]):
                raise ValueError("blind transcript/action text contains a visible identity, group, phase, or date marker; redact and review it first")
        if item["teacher_timecode"] is not None and not re.fullmatch(r"\d{1,2}:\d{2}", str(item["teacher_timecode"])):
            raise ValueError("teacher_timecode must be M:SS or null")
        clean["opportunities"].append(item)
    return clean


def blank_rating(clip: dict, rater_code: str) -> dict:
    if rater_code not in {"R1", "R2"}:
        raise ValueError("rater_code must be R1 or R2")
    clean_clip = validate_blind_clip(clip)
    return {
        "clip_id": clean_clip["clip_id"],
        "rater_code": rater_code,
        "opportunities": [
            {**row, "scores": {dimension: None for dimension in DIMENSIONS}, "rationale": "",
             "rationales": {dimension: "" for dimension in DIMENSIONS},
             "missing_reason": MISSING_REASONS.get(row["status"], "")}
            for row in clean_clip["opportunities"]
        ],
        "submitted_at": None,
    }


def score_rater(record: dict) -> dict:
    """Validate one rater's form and calculate equal-weighted 4-20 score."""
    if record.get("rater_code") not in {"R1", "R2"}:
        raise ValueError("unknown rater code")
    rows = record.get("opportunities")
    if not isinstance(rows, list) or len(rows) != OPPORTUNITY_COUNT:
        raise ValueError("exactly two opportunity records are required")
    values: dict[str, list[int]] = defaultdict(list)
    missing = []
    for expected, row in enumerate(rows, 1):
        if row.get("opportunity_no") != expected:
            raise ValueError("opportunity order is invalid")
        status = row.get("status", "present")
        if status != "present":
            if status not in MISSING_REASONS or row.get("missing_reason") != MISSING_REASONS[status]:
                raise ValueError("a documented missing reason is required; do not substitute zero")
            if any(value is not None for value in (row.get("scores") or {}).values()):
                raise ValueError("missing opportunities must not contain ratings")
            if any(str(value or "").strip() for value in (row.get("rationales") or {}).values()):
                raise ValueError("missing opportunities must not contain scoring rationales")
            missing.append(expected)
            continue
        scores = row.get("scores") or {}
        if set(scores) != set(DIMENSIONS):
            raise ValueError("all four rubric dimensions must be present")
        for dimension in DIMENSIONS:
            value = scores[dimension]
            if type(value) is not int or not 1 <= value <= 5:
                raise ValueError("present opportunity scores must be integers 1-5; null is only for documented missingness")
            values[dimension].append(value)
        rationales = row.get("rationales") or {}
        if set(rationales) != set(DIMENSIONS) or any(not str(rationales[d] or "").strip() for d in DIMENSIONS):
            raise ValueError("each dimension score requires its own video-grounded rationale")
    means = {dimension: (sum(values[dimension]) / len(values[dimension]) if values[dimension] else None)
             for dimension in DIMENSIONS}
    complete = not missing and all(value is not None for value in means.values())
    return {
        "clip_id": record.get("clip_id"),
        "rater_code": record["rater_code"],
        "dimension_means": means,
        "session_total": sum(means.values()) if complete else None,
        "complete": complete,
        "missing_opportunities": missing,
        "submitted_at": record.get("submitted_at"),
    }


def aggregate_raters(records: list[dict]) -> list[dict]:
    """Aggregate only after two separately submitted records exist."""
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        result = score_rater(record)
        clip_id, rater = result["clip_id"], result["rater_code"]
        if (not isinstance(clip_id, str) or not BLIND_ID.fullmatch(clip_id)
                or BLIND_SEMANTIC_TOKEN.search(clip_id)):
            raise ValueError("rating clip ID is not anonymous/opaque")
        if rater in grouped[clip_id]:
            raise ValueError("duplicate submission for a rater and clip")
        grouped[clip_id][rater] = result
    output = []
    for clip_id in sorted(grouped):
        raters = grouped[clip_id]
        ready = all(code in raters for code in ("R1", "R2"))
        both_complete = ready and all(raters[code]["complete"] for code in ("R1", "R2"))
        mean_total = (raters["R1"]["session_total"] + raters["R2"]["session_total"]) / 2 if both_complete else None
        output.append({
            "clip_id": clip_id,
            "status": "complete" if both_complete else "pending_second_rater" if not ready else "incomplete_key_opportunity",
            "rater_totals": {code: raters[code]["session_total"] if code in raters else None for code in ("R1", "R2")},
            "coordinator_mean_total": mean_total,
            "dimension_means_by_rater": {code: raters[code]["dimension_means"] if code in raters else None for code in ("R1", "R2")},
            "missing_opportunities_by_rater": {code: raters[code]["missing_opportunities"] if code in raters else None for code in ("R1", "R2")},
            "submission_times": {code: raters[code]["submitted_at"] if code in raters else None for code in ("R1", "R2")},
        })
    return output


def ratings_csv(records: list[dict]) -> str:
    """Portable long-format export; no identities, group, phase, or source filename."""
    fields = ["clip_id", "rater_code", "opportunity_no", "start_timecode", "status", "student_quote",
              "teacher_action_quote_or_description", "teacher_timecode", *DIMENSIONS,
              *(f"{dimension}_评分依据" for dimension in DIMENSIONS), "missing_reason", "submitted_at"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for record in records:
        for row in record["opportunities"]:
            item = {key: record.get(key) for key in ("clip_id", "rater_code", "submitted_at")}
            item.update({key: row.get(key) for key in fields if key in row})
            item.update(row.get("scores") or {})
            item.update({f"{dimension}_评分依据": (row.get("rationales") or {}).get(dimension, "")
                         for dimension in DIMENSIONS})
            writer.writerow(item)
    return buffer.getvalue()


def coordinator_capture_summary(*, teacher_finalized_segments: int, student_generated: int,
                                playback_started: int, playback_completed: int,
                                hand_observed_samples: int, hand_total_samples: int,
                                hand_source: str) -> dict:
    if any(type(x) is not int or x < 0 for x in (teacher_finalized_segments, student_generated, playback_started,
                                                   playback_completed, hand_observed_samples, hand_total_samples)):
        raise ValueError("capture counts must be non-negative integers")
    if hand_observed_samples > hand_total_samples:
        raise ValueError("observed hand samples cannot exceed total samples")
    return {
        "teacher_finalized_segments": {"count": teacher_finalized_segments, "source": "classroom transcript final events"},
        "student_reply_generated": {"count": student_generated, "source": "student generation events"},
        "playback_started": {"count": playback_started, "source": "client playback_started receipts; missing remains missing"},
        "playback_completed": {"count": playback_completed, "source": "client playback_completed receipts"},
        "hand_visibility": {"observed_samples": hand_observed_samples, "total_samples": hand_total_samples,
                            "rate": round(hand_observed_samples / hand_total_samples, 6) if hand_total_samples else None,
                            "source": hand_source,
                            "interpretation": "sample coverage only; not teaching quality or share of lesson time"},
    }


def build_coordinator_export(study_metadata: dict, rounds: dict) -> dict:
    """Assemble coordinator-only records without inventing absent values.

    `study_metadata` contains the coordinator's already-authorized roster and
    delivery log. `rounds` maps round1/round2 to the source event arrays.
    Participant identity, assignment, stage, dates, self-review, and goals are
    intentionally retained here; this export must never be used as a rater pack.
    """
    if not isinstance(study_metadata, dict) or not isinstance(rounds, dict):
        raise ValueError("coordinator metadata and rounds are required")
    participant_code = study_metadata.get("participant_code")
    if not isinstance(participant_code, str) or not re.fullmatch(r"P\d{2}", participant_code):
        raise ValueError("coordinator export requires the assigned P01-P16 study code")
    group = study_metadata.get("group")
    if group not in {"transcript", "multimodal"}:
        raise ValueError("coordinator group must be transcript or multimodal")
    if set(rounds) != {"round1", "round2"}:
        raise ValueError("provide both study rounds; leave unknown values null rather than inferring")
    session_rows = []
    for stage in ("round1", "round2"):
        source = rounds[stage]
        if not isinstance(source, dict) or not isinstance(source.get("events"), list):
            raise ValueError("each round requires its source event list")
        events = source["events"]
        student_ids = {str((e.get("data") or {}).get("reply_id")) for e in events if e.get("type") == "student"}
        starts = [e for e in events if e.get("type") == "playback" and (e.get("data") or {}).get("status") == "playback_started"]
        completions = [e for e in events if e.get("type") == "playback" and (e.get("data") or {}).get("status") == "playback_completed"]
        started_replies = {str((e.get("data") or {}).get("reply_id")) for e in starts
                           if (e.get("data") or {}).get("reply_id") not in (None, "")}
        completed_replies = {str((e.get("data") or {}).get("reply_id")) for e in completions
                             if (e.get("data") or {}).get("reply_id") not in (None, "")}
        motion = [e for e in events if e.get("type") == "pose"]
        hand_seen = sum(1 for e in motion if ((e.get("data") or {}).get("hands") or {}).get("status") == "observed")
        session_rows.append({
            "stage": stage,
            "classroom_session_id": source.get("classroom_session_id"),
            "material_version": source.get("material_version"),
            "actual_at": source.get("actual_at"),
            "event_counts": {
                "teacher_finalized_segments": sum(e.get("type") == "transcript" for e in events),
                "student_replies_generated": len(student_ids - {"None", ""}),
                "playback_started": len(starts),
                "playback_completed": len(completions),
                "playback_start_missing_for_completed_replies": len(completed_replies - started_replies),
                "hand_observed_samples": hand_seen,
                "hand_total_samples": len(motion),
                "hand_observation_rate": round(hand_seen / len(motion), 6) if motion else None,
            },
            "self_review": source.get("self_review"),
            "report_text_issued": source.get("report_text_issued"),
            "report_issued_at": source.get("report_issued_at"),
            "input_sha256": source.get("input_sha256"),
            "model": source.get("model"),
            "rubric_version": source.get("rubric_version"),
            "template_version": source.get("template_version"),
            "participant_revision_goal": source.get("participant_revision_goal"),
        })
    interval_days = study_metadata.get("interval_days")
    if interval_days is not None and (type(interval_days) is not int or interval_days < 0):
        raise ValueError("interval_days must be a non-negative integer or null")
    cross_round = study_metadata.get("cross_round_followup") or []
    allowed_status = {"no_opportunity", "opportunity_provided_teacher_skipped", "cannot_assess", "teacher_response_observed"}
    if not isinstance(cross_round, list) or any(not isinstance(item, dict) or item.get("status") not in allowed_status for item in cross_round):
        raise ValueError("cross-round follow-up status must distinguish no opportunity, skipped response, and cannot assess")
    return {
        "participant_code": participant_code,
        "group": group,
        "prior_teaching_experience_stratum": study_metadata.get("prior_teaching_experience_stratum"),
        "form_order": study_metadata.get("form_order"),
        "actual_interval_days": interval_days,
        "rounds": session_rows,
        "cross_round_followup": cross_round,
    }
