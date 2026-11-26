from datetime import datetime, timedelta
import pytest
from extensions import db
from classroom_models import Classroom, ClassroomEvent
from services import classroom_reports as reports
from services.classroom_readiness import report_readiness
from test_classroom_base import app
from test_classroom_runtime import live
from test_classroom_api import headers


def sufficient_events():
    events = [
        {'id': 1, 'at_ms': 1000, 'type': 'transcript', 'data': {'text': '把同一个整体平均分成两份，每份就是这个整体的二分之一。分母表示平均分的份数，分子表示取了其中几份。'}},
        {'id': 2, 'at_ms': 8000, 'type': 'transcript', 'data': {'text': '小林，请说说为什么这里必须先强调同一个整体和平均分，大小不同的蛋糕的一半是否一定一样多？'}},
        {'id': 3, 'at_ms': 9000, 'type': 'student', 'data': {'reply_id': 'r1', 'text': '必须是同一个整体平均分，不同大小的蛋糕的一半不一定一样多。'}},
        {'id': 4, 'at_ms': 15000, 'type': 'playback', 'data': {'reply_id': 'r1', 'status': 'playback_completed'}},
    ]
    for i, at in enumerate([2000, 4100, 6200], 5):
        events.append({'id': i, 'type': 'pose', 'at_ms': at, 'data': {
            'motion_version': 2, 'body': {'status': 'observed', 'confidence': .9, 'scope': 'upper_body'},
            'hands': {'status': 'disabled'}, 'face': {'status': 'disabled'}}})
    return events


def seed_sufficient(sid):
    for e in sufficient_events():
        db.session.add(ClassroomEvent(session_id=sid, event_key=f"fixture-{e['id']}",
            kind=e['type'], at_ms=e['at_ms'], payload=e['data']))
    db.session.commit()


def test_report_gate_all_reasons_and_success():
    empty = report_readiness([], 9)
    assert not empty['eligible']
    assert {c['key'] for c in empty['checks'] if not c['passed']} == {'duration', 'transcript', 'interaction', 'motion', 'scene'}
    missing = report_readiness([], 30)
    assert missing['eligible'] and len(missing['reasons']) == 4
    good = report_readiness(sufficient_events(), 30)
    assert good['eligible'] and good['reasons'] == []
    assert good['scene_mode'] == 'local_teacher_frame'


@pytest.mark.parametrize('kind', ['missing_playback', 'interrupted', 'failed', 'too_short', 'future', 'low_confidence', 'multiple', 'cloud_missing'])
def test_missing_or_failed_evidence_is_a_textual_gap_not_a_report_gate(kind):
    events = sufficient_events()
    if kind == 'missing_playback': events = [e for e in events if e['type'] != 'playback']
    if kind in ('interrupted', 'failed'):
        events.append({'id': 10, 'type': 'interrupt' if kind == 'interrupted' else 'playback', 'at_ms': 16000,
                       'data': {'reply_id': 'r1', 'status': 'playback_failed'}})
    if kind == 'too_short':
        for e in events:
            if e['type'] == 'transcript': e['data']['text'] = '你好！'
    if kind == 'future':
        for e in events: e['at_ms'] += 60000
    if kind in ('low_confidence', 'multiple'):
        for e in events:
            if e['type'] == 'pose': e['data']['body']['status'] = kind
    result = report_readiness(events, 30, cloud_vision=kind == 'cloud_missing')
    assert result['eligible']
    assert result['reasons'] or kind in ('low_confidence', 'multiple')
    if kind in ('low_confidence', 'multiple', 'cloud_missing'):
        assert not result['dimension_eligibility']['posture']


def test_empty_or_invalid_cloud_observations_do_not_count():
    events = sufficient_events()
    for value in ('', '   ', [], None):
        cloud = {'id': 20, 'type': 'vision', 'at_ms': 20000, 'data': {'confidence': .9, 'scene_detected': True, 'observations': value}}
        assert not report_readiness(events + [cloud], 30, cloud_vision=True)['dimension_eligibility']['posture']
    cloud['data']['observations'] = '画面中可见一位教师正在展示两块等大的纸片。'
    assert report_readiness(events + [cloud], 30, cloud_vision=True)['eligible']
    for detected in (False, 'true', None):
        cloud['data']['scene_detected'] = detected
        assert not report_readiness(events + [cloud], 30, cloud_vision=True)['dimension_eligibility']['posture']


def test_finish_ten_seconds_enforced_for_rest_and_websocket(app):
    obj = live(app)
    room = db.session.get(Classroom, obj.sid)
    room.started_at = obj.start = datetime.utcnow()
    db.session.commit()
    response = app.test_client().post(f'/api/classroom/sessions/{obj.sid}/finish', headers=headers(1))
    assert response.status_code == 409 and response.json['minimum_seconds'] == 10
    assert room.state == 'active'
    obj.incoming({'type': 'finish', 'event_id': 'early'})
    assert not obj.finish_requested and obj.ws.messages[-1]['type'] == 'error'
    obj.start -= timedelta(seconds=10)
    room.started_at = obj.start
    db.session.commit()
    obj.incoming({'type': 'finish', 'event_id': 'on-time'})
    assert obj.finish_requested


def test_missing_evidence_is_reported_but_does_not_block_generation(app, monkeypatch):
    obj = live(app)
    readiness = report_readiness([], 30, False)
    assert readiness['eligible'] is True
    assert len(readiness['reasons']) == 4
    monkeypatch.setattr(reports, 'report_theory_context', lambda **kwargs: ([], {}))
    monkeypatch.setattr(reports, 'chat', lambda *args, **kwargs: {'coaching_focuses': []})
    url = f'/api/classroom/sessions/{obj.sid}'
    client = app.test_client()
    client.post(url + '/finish', headers=headers(1))
    data = client.get(url, headers=headers(1)).json
    assert len(data['report_readiness']['reasons']) == 4
    from test_classroom_jobs import wait_for_report
    row = wait_for_report(obj.sid)
    assert row.report_state == 'completed' and row.report is not None
    assert row.report['data_readiness']['reasons']


def test_camera_consent_is_required_before_creating_session(app):
    obj = live(app)
    client = app.test_client()
    for value in (None, False, 'true'):
        result = client.post('/api/classroom/sessions', headers=headers(1), json={'audio_consent': True, 'camera_consent': value})
        assert result.status_code == 400 and '摄像头' in result.json['message']
