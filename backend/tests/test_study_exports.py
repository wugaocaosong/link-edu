from services.study_exports import (
    DIMENSIONS,
    aggregate_raters,
    build_coordinator_export,
    build_feedback_evidence,
    build_sealed_input,
    classify_cross_round_followup,
    coordinator_capture_summary,
    make_participant_delivery,
    score_rater,
    seal_packet,
    validate_blind_clip,
)
from services.study_export_review import StudyReviewError, build_study_messages, generate_study_review, validate_and_render


def event(event_id, kind, at_ms, **data):
    return {"id": event_id, "type": kind, "at_ms": at_ms, "data": data}


def recording(clip_id="K7M4Q2"):
    return {
        "clip_id": clip_id,
        "participant_id": "P09",
        "group": "multimodal",
        "phase": "posttest",
        "date": "2026-11-25",
        "source_filename": "P09_post_multimodal_20261125.mp4",
        "opportunities": [
            {"opportunity_no": 1, "start_timecode": "0:12", "student_quote": "我觉得是二分之一。",
             "teacher_action_quote_or_description": "教师追问判断依据。", "teacher_timecode": "0:20"},
            {"opportunity_no": 2, "start_timecode": "2:31", "student_quote": "只要分成两块，每块就是一半。",
             "teacher_action_quote_or_description": "教师请学生比较两份。", "teacher_timecode": "2:42"},
        ],
    }


def rated(code="R1", missing_second=False):
    rows = []
    for n in (1, 2):
        if missing_second and n == 2:
            rows.append({"opportunity_no": 2, "status": "opportunity_not_provided",
                         "scores": {dimension: None for dimension in DIMENSIONS},
                         "rationale": "", "rationales": {dimension: "" for dimension in DIMENSIONS},
                         "missing_reason": "主持人未提供该回应机会"})
        else:
            rows.append({"opportunity_no": n, "status": "present",
                         "scores": {dimension: (n + 2) for dimension in DIMENSIONS},
                         "rationale": f"可核对的第{n}次回应依据",
                         "rationales": {dimension: f"第{n}次录像支持{dimension}分项。" for dimension in DIMENSIONS}})
    return {"clip_id": "K7M4Q2", "rater_code": code, "opportunities": rows, "submitted_at": "synthetic-test"}


def test_complete_scoring_equal_weights_and_total_4_to_20():
    result = score_rater(rated())
    assert result["complete"] is True
    assert result["dimension_means"] == {dimension: 3.5 for dimension in DIMENSIONS}
    assert result["session_total"] == 14


def test_missing_one_opportunity_stays_null_and_withholds_total():
    result = score_rater(rated(missing_second=True))
    assert result["complete"] is False
    assert result["missing_opportunities"] == [2]
    assert result["session_total"] is None
    assert result["dimension_means"] == {dimension: 3 for dimension in DIMENSIONS}


def test_single_rater_is_pending_second_submission():
    result = aggregate_raters([rated()])[0]
    assert result["status"] == "pending_second_rater"
    assert result["rater_totals"]["R1"] == 14
    assert result["rater_totals"]["R2"] is None
    assert result["coordinator_mean_total"] is None


def test_two_complete_raters_average_only_after_both_submit():
    first = rated("R1")
    second = rated("R2")
    second["opportunities"][0]["scores"] = {dimension: 4 for dimension in DIMENSIONS}
    second["opportunities"][1]["scores"] = {dimension: 5 for dimension in DIMENSIONS}
    result = aggregate_raters([first, second])[0]
    assert result["status"] == "complete"
    assert result["coordinator_mean_total"] == 16


def test_transcript_and_multimodal_inputs_share_same_transcript_but_not_extra_inputs():
    events = [
        event(1, "transcript", 1000, text="我把纸平均分成两份。"),
        event(2, "student", 2000, reply_id="played", text="我觉得占一半。"),
        event(3, "playback", 2300, reply_id="played", status="playback_started"),
        event(4, "playback", 4900, reply_id="played", status="playback_completed"),
        event(5, "student", 5500, reply_id="not-played", text="仅生成、没有播放的内容"),
        event(6, "playback", 7000, reply_id="not-played", status="playback_failed"),
        event(7, "pose", 9000, motion_version=2),
    ]
    motion = [{"event_id": 7, "at_ms": 9000, "modality": "hands", "observation": "手部可观察", "source": "local"}]
    transcript = build_sealed_input("transcript", events, motion)
    multimodal = build_sealed_input("multimodal", events, motion)
    assert transcript["transcript"] == multimodal["transcript"]
    assert "playback" not in transcript and "teacher_motion" not in transcript
    assert multimodal["playback"] == [
        {"reply_id": "played", "status": "playback_started", "at_ms": 2300},
        {"reply_id": "played", "status": "playback_completed", "at_ms": 4900},
        {"reply_id": "not-played", "status": "playback_failed", "at_ms": 7000},
    ]
    assert "仅生成、没有播放的内容" not in str(transcript)
    assert "仅生成、没有播放的内容" not in str(multimodal)
    assert multimodal["teacher_motion"] == [{k: v for k, v in motion[0].items() if k != "source"}]


def test_packet_hash_is_over_only_model_input():
    packet = seal_packet("transcript", "SESSION-X", [event(1, "transcript", 10, text="定稿")],
                         model="deepseek-v4-flash", rubric_version="fraction-formative-1",
                         template_version="fraction-narrative-1")
    assert packet["input_sha256"]
    assert "group" not in packet["input"]
    assert "session_id" not in packet["input"]


def test_blind_clip_whitelists_identity_group_phase_date_and_source_filename():
    blind = validate_blind_clip(recording())
    serialized = str(blind)
    for private in ("P09", "multimodal", "posttest", "2026-11-25", "source_filename"):
        assert private not in serialized
    assert blind["clip_id"] == "K7M4Q2"


def test_blind_clip_rejects_semantic_identity_in_filename_safe_id_and_wrong_opportunity_count():
    bad_id = recording("P09POST")
    try:
        validate_blind_clip(bad_id)
    except ValueError:
        pass
    else:
        raise AssertionError("participant-like IDs must be rejected")
    bad_rows = recording()
    bad_rows["opportunities"] = bad_rows["opportunities"][:1]
    try:
        validate_blind_clip(bad_rows)
    except ValueError:
        pass
    else:
        raise AssertionError("two opportunities are required")
    dated = recording()
    dated["opportunities"][0]["student_quote"] = "2026-11-25，我觉得是二分之一。"
    try:
        validate_blind_clip(dated)
    except ValueError:
        pass
    else:
        raise AssertionError("visible date metadata in blind transcript must be rejected")


def test_missing_playback_start_is_not_backfilled_from_generation_or_completion():
    summary = coordinator_capture_summary(teacher_finalized_segments=64, student_generated=16,
        playback_started=0, playback_completed=16, hand_observed_samples=15,
        hand_total_samples=263, hand_source="local motion samples")
    assert summary["playback_started"]["count"] == 0
    assert summary["playback_started"]["source"].startswith("client playback_started")
    assert summary["playback_completed"]["count"] == 16
    assert summary["hand_visibility"]["observed_samples"] == 15
    assert summary["hand_visibility"]["total_samples"] == 263
    assert summary["hand_visibility"]["interpretation"].startswith("sample coverage only")


def test_ratings_reject_zero_and_missing_without_reason():
    data = rated()
    data["opportunities"][0]["scores"][DIMENSIONS[0]] = 0
    try:
        score_rater(data)
    except ValueError:
        pass
    else:
        raise AssertionError("0 is not a rating")
    data = rated(missing_second=True)
    data["opportunities"][1]["missing_reason"] = ""
    try:
        score_rater(data)
    except ValueError:
        pass
    else:
        raise AssertionError("missingness requires a reason")


def test_feedback_trace_requires_played_student_quote_and_immediate_teacher_followup():
    events = [
        event(10, "student", 1000, reply_id="r", text="我觉得是二分之一。"),
        event(11, "playback", 1500, reply_id="r", status="playback_completed"),
        event(12, "transcript", 1800, text="你是怎么判断的？"),
    ]
    rows = build_feedback_evidence(events, [{
        "student_event_id": 10, "teacher_event_id": 12, "student_claim_type": "conclusion_only",
        "what_response_did": "教师追问了判断依据，但后续学生说明未包含在此引用链。",
        "next_step": "等待学生补充依据后，请其比较两份大小是否相同。",
    }])
    assert rows[0]["student"]["quote"] == "我觉得是二分之一。"
    assert rows[0]["teacher"]["quote"] == "你是怎么判断的？"
    assert rows[0]["next_step_source"].startswith("AI suggestion")
    events[1]["data"]["status"] = "playback_failed"
    try:
        build_feedback_evidence(events, [{
            "student_event_id": 10, "teacher_event_id": 12, "student_claim_type": "conclusion_only",
            "what_response_did": "不可引用", "next_step": "不可给建议",
        }])
    except ValueError:
        pass
    else:
        raise AssertionError("unplayed virtual student text cannot be reported as heard")


def test_delivery_requires_self_review_first_and_retains_exact_text_and_versions():
    events = [event(10, "student", 1000, reply_id="r", text="我觉得是二分之一。"),
              event(11, "playback", 1500, reply_id="r", status="playback_completed"),
              event(12, "transcript", 1800, text="你是怎么判断的？")]
    selections = [{"student_event_id": 10, "teacher_event_id": 12, "student_claim_type": "conclusion_only",
                   "what_response_did": "教师追问依据。", "next_step": "请学生说明并检验两份是否等大。"}]
    report_text = (
        "精确发放原文。"
        + "请继续核对本次课堂目标与学生的理解线索，并在下一次练习中留出等待学生说明依据的时间。" * 7
        + "\n学生原话：我觉得是二分之一。\n教师随后说：你是怎么判断的？\n教师回应：教师追问依据。\n下次可尝试：请学生说明并检验两份是否等大。"
    )
    required = dict(events=events, evidence_selections=selections, report_text=report_text, issued_at="t2",
                    input_sha256="a" * 64, model="deepseek-v4-flash", rubric_version="fraction-formative-1",
                    template_version="fraction-narrative-1")
    try:
        make_participant_delivery(self_review={}, **required)
    except ValueError:
        pass
    else:
        raise AssertionError("report delivery must follow a saved independent self-review")
    delivery = make_participant_delivery(self_review={"text": "我的自评", "saved_at": "t1"}, **required)
    assert delivery["report_text"] == report_text
    assert delivery["self_review"]["text"] == "我的自评"
    assert delivery["issued_at"] == "t2"
    assert delivery["model"] == "deepseek-v4-flash"
    assert len(delivery["evidence_sequences"]) == 1


def test_cross_round_keeps_no_opportunity_skipped_and_cannot_assess_distinct():
    assert classify_cross_round_followup(opportunity_status="not_provided") == "no_opportunity"
    assert classify_cross_round_followup(opportunity_status="provided", teacher_response_observed=False) == "opportunity_provided_teacher_skipped"
    assert classify_cross_round_followup(opportunity_status="provided", evidence_sufficient=False) == "cannot_assess"


def test_model_prompt_receives_only_group_input_and_cannot_change_frozen_versions():
    packet = seal_packet("transcript", "PRIVATE-SESSION", [event(1, "transcript", 1000, text="老师定稿")],
        model="deepseek-v4-flash", rubric_version="fraction-formative-1", template_version="fraction-narrative-1")
    messages = build_study_messages(packet)
    assert "PRIVATE-SESSION" not in messages[1]["content"]
    assert '"group"' not in messages[1]["content"]
    assert '"transcript"' in messages[1]["content"]
    packet["input"]["self_review"] = "private reflection"
    try:
        build_study_messages(packet)
    except StudyReviewError:
        pass
    else:
        raise AssertionError("mutated/hash-mismatched model input must not be sent")


def test_generated_report_uses_verbatim_quotes_and_rejects_invalid_event_citations():
    events = [event(10, "student", 1000, reply_id="r", text="我觉得是二分之一。"),
              event(11, "playback", 1500, reply_id="r", status="playback_completed"),
              event(12, "transcript", 1800, text="你是怎么判断的？")]
    explanation = ("教师在学生完整表达后追问判断依据，但该回应链没有记录学生后续说明，因此不能据此认定其理解已得到检验。"
                   "这一步体现了从确认答案转向了解判断依据；目前还看不到教师是否进一步承接学生理由或调整解释。")
    next_step = ("下次可以先请学生说出判断理由，再让学生比较纸带两份是否等大，最后请其用自己的话说明为什么只有等分后取一份才能表示二分之一。"
                 "如果学生仍只报出答案，可让他指着图说出整体、份数和取出的部分，再用另一张不等分纸带检验判断是否改变。"
                 "教师可先等待学生完整表达，不急于复述规则；学生说出理由后，再请他指出哪两份要比较，并说明比较结果如何影响最初的判断。")
    generated = validate_and_render({"sequences": [{"student_event_id": 10, "teacher_event_id": 12,
        "student_claim_type": "conclusion_only", "what_response_did": explanation, "next_step": next_step}]}, events)
    assert "我觉得是二分之一。" in generated["report_text"]
    assert "你是怎么判断的？" in generated["report_text"]
    assert len(generated["report_text"]) >= 280
    assert generated["evidence_selections"][0]["student_event_id"] == 10
    try:
        validate_and_render({"sequences": [{"student_event_id": 10, "teacher_event_id": 999,
            "student_claim_type": "conclusion_only", "what_response_did": explanation, "next_step": next_step}]}, events)
    except ValueError:
        pass
    else:
        raise AssertionError("uncited teacher claims must be rejected")


def test_model_call_uses_frozen_parameters_and_sends_no_outer_metadata():
    import json
    from types import SimpleNamespace
    events = [event(10, "student", 1000, reply_id="r", text="我觉得是二分之一。"),
              event(11, "playback", 1500, reply_id="r", status="playback_completed"),
              event(12, "transcript", 1800, text="你是怎么判断的？")]
    packet = seal_packet("transcript", "HIDDEN-SESSION", events, model="deepseek-v4-flash",
        rubric_version="fraction-formative-1", template_version="fraction-narrative-1")
    suggestion = "请学生先给出判断依据，再比较两份纸带是否等大，并用另一种图示核验其能否说明同一个整体、平均分成若干份和取其中一份的关系。"
    explanation = ("教师追问了判断依据；在当前片段里还没有记录学生后续回答，因而不能判断其解释是否澄清，也不能据此说教师已经检验了理解。"
                   "学生当前只表达了结论，证据尚未呈现他如何判断两份是否等大。")
    suggestion = suggestion + "请根据学生新的说明继续追问，并确认他能否把刚才的判断方法迁移到一个新的等分或不等分图示。" * 3
    payload = {"sequences": [{"student_event_id": 10, "teacher_event_id": 12,
        "student_claim_type": "conclusion_only", "what_response_did": explanation, "next_step": suggestion}]}
    capture = {}

    class Completions:
        def create(self, **kwargs):
            capture.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False)))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    result = generate_study_review(packet, events, api_key="test-key", client=client)
    assert capture["model"] == "deepseek-v4-flash"
    assert capture["temperature"] == 0 and capture["top_p"] == 1 and capture["max_tokens"] == 1200
    assert capture["response_format"] == {"type": "json_object"}
    assert capture["extra_body"] == {"thinking": {"type": "disabled"}}
    user_content = capture["messages"][1]["content"]
    assert "HIDDEN-SESSION" not in user_content and '"group"' not in user_content
    assert result["input_sha256"] == packet["input_sha256"]


def test_blind_cli_writes_two_separate_whitelisted_files(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path
    source = tmp_path / "source.json"
    source.write_text(json.dumps(recording(), ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "pack"
    script = Path(__file__).resolve().parents[2] / "scripts" / "study_export.py"
    subprocess.run([sys.executable, str(script), "blind", "--input", str(source), "--out-dir", str(output)], check=True)
    files = sorted(output.glob("*.json"))
    assert [path.name for path in files] == ["blind_K7M4Q2_R1.json", "blind_K7M4Q2_R2.json"]
    for path in files:
        content = path.read_text(encoding="utf-8")
        for forbidden in ("P09", "multimodal", "posttest", "2026-11-25", "source_filename"):
            assert forbidden not in content
        assert len(json.loads(content)["opportunities"]) == 2


def test_coordinator_export_preserves_exact_delivery_and_actual_denominators():
    rounds = {}
    for name, base in (("round1", 10), ("round2", 20)):
        rounds[name] = {"classroom_session_id": base, "material_version": "fraction-card-1",
            "actual_at": None, "self_review": None, "report_text_issued": None,
            "report_issued_at": None, "input_sha256": None, "model": None,
            "rubric_version": None, "template_version": None, "participant_revision_goal": None,
            "events": [event(1, "student", 1000, reply_id="r1", text="发言"),
                       event(2, "playback", 1300, reply_id="r1", status="playback_completed"),
                       event(3, "pose", 2000, hands={"status": "observed"}),
                       event(4, "pose", 4000, hands={"status": "no_detection"})]}
    metadata = {"participant_code": "P03", "group": "multimodal", "interval_days": None,
        "cross_round_followup": [{"status": "no_opportunity"}]}
    result = build_coordinator_export(metadata, rounds)
    row = result["rounds"][0]
    assert row["event_counts"]["playback_started"] == 0
    assert row["event_counts"]["playback_completed"] == 1
    assert row["event_counts"]["playback_start_missing_for_completed_replies"] == 1
    assert row["event_counts"]["hand_observed_samples"] == 1
    assert row["event_counts"]["hand_total_samples"] == 2
    assert row["report_text_issued"] is None
    assert result["cross_round_followup"] == [{"status": "no_opportunity"}]
