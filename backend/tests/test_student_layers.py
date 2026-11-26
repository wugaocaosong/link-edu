from services.classroom_student_layers import (
    choose_cue, constrain_disclosure, reason_status, silence_audio, utterance_plan,
)
from services.fraction_study import study_evidence


def test_casual_question_does_not_reveal_the_hidden_reason():
    cue = choose_cue('round1', 'yu', '这表示什么？', [])
    assert cue['step'] == 'challenge'
    assert constrain_disclosure('yu', 'challenge', '因为我数了两份，所以是一半。') == '这两份不一样大，不也是一半吗？'
    assert choose_cue('round1', 'yu', '你为什么这样想？', [])['step'] == 'reason'
    assert choose_cue('round1', 'lin', '不对。', ['conclusion'])['step'] == 'shallow'


def test_second_round_opens_with_the_biased_reason_on_a_different_material():
    first = choose_cue('round1', 'lin', '谁来说说？', [])
    second = choose_cue('round2', 'yu', '谁来说说？', [])
    assert first['step'] == 'conclusion' and first['material'] == '折纸'
    assert second['step'] == 'reason' and second['material'] == '纸带'
    told = choose_cue('round2', 'yu', '平均分就是每份一样大。', [])
    assert told['step'] == 'shallow'


def test_verifier_waits_for_a_comparison_before_transferring():
    assert choose_cue('round1', 'ming', '为什么？', [])['step'] == 'stable'
    assert choose_cue('round1', 'ming', '我们来比一比。', [], ['scaffold'])['step'] == 'transfer'
    assert '纸带' in constrain_disclosure('ming', 'transfer', '我已经知道了。', 'round1')
    assert '一张纸' in constrain_disclosure('ming', 'transfer', '我已经知道了。', 'round2')


def test_reason_line_has_a_pause_before_the_reason_span():
    plan = utterance_plan('reason', '我数了两份，所以我觉得这一块就是一半。')
    assert [item['kind'] for item in plan] == ['claim', 'reason']
    assert plan[1]['pause_before_ms'] >= 400
    assert utterance_plan('conclusion', '我觉得这一份是一半。')[0]['kind'] == 'claim'
    assert len(silence_audio(480, 24000)) > 100


def test_interruption_timing_distinguishes_an_unfinished_reason():
    clock = {'reason_start_ms': 800, 'audio_ms': 1600}
    assert reason_status(clock, None, 10) == 'not_started'
    assert reason_status(clock, 10.0, 10.2) == 'not_started'
    assert reason_status(clock, 10.0, 10.9) == 'cut_off'
    assert reason_status(clock, 10.0, 11.5) == 'heard'
    assert reason_status({'audio_ms': 400}, 10.0, 10.2) == 'no_reason'


def test_multimodal_packet_keeps_the_reason_cut_status():
    events = [
        {'id': 1, 'at_ms': 1, 'type': 'student', 'data': {'student_id': 'yu', 'reply_id': 'b', 'text': '我数了两份，所以是一半。'}},
        {'id': 2, 'at_ms': 2, 'type': 'playback_onset', 'data': {'reply_id': 'b'}},
        {'id': 3, 'at_ms': 3, 'type': 'interrupt', 'data': {'reply_id': 'b', 'reason_status': 'cut_off'}},
        {'id': 4, 'at_ms': 4, 'type': 'playback', 'data': {'reply_id': 'b', 'status': 'playback_completed'}},
    ]
    packet, _ = study_evidence(events, 'multimodal')
    assert packet['playback'][0]['reason_status'] == 'cut_off'
    assert 'reason_status' not in study_evidence(events, 'transcript')[0]
