import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from classroom_models import Classroom, ClassroomEvent
from extensions import db
from models import User
from services.classroom_providers import ProviderError
from services.fraction_study import allocate, capture_summary, constrain_line, student_cue, study_evidence
from services.study_review import (
    MODEL, SYSTEM, TEMPERATURE, compile_review, issue_document, render, user_content, validate_issue,
)
from study_models import StudyAttempt, StudyParticipant
from tenancy import personal_tenant_for
from test_classroom_api import headers
from test_classroom_base import app


def test_migrations_target_flask_instance_for_relative_sqlite(tmp_path, monkeypatch):
    import app as app_module
    from alembic import command
    from alembic.config import Config
    from flask import Flask
    from sqlalchemy import inspect, text

    flask_app = Flask('study-migration', instance_path=str(tmp_path/'instance'))
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///relative.db'
    db.init_app(flask_app)
    monkeypatch.setattr(app_module, 'app', flask_app)
    monkeypatch.chdir(tmp_path)
    cfg = Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
    with flask_app.app_context():
        db.metadata.create_all(db.engine, tables=[t for t in db.metadata.sorted_tables
                                                   if not t.name.startswith('study_')])
        command.stamp(cfg,'20261120_01')
        command.upgrade(cfg,'head')
        assert not (tmp_path/'relative.db').exists()
        with db.engine.connect() as conn:
            assert conn.execute(text('select version_num from alembic_version')).scalar()=='20261123_01'
        command.downgrade(cfg,'20261120_01')
        assert 'study_attempts' not in inspect(db.engine).get_table_names()
        db.engine.dispose()


@pytest.mark.parametrize('experienced', range(17))
def test_allocation(experienced):
    rows = allocate([{'user_id':i, 'experience':i < experienced} for i in range(16)], random.Random(42))
    for arm in ('multimodal','transcript'):
        group = [r for r in rows if r['arm'] == arm]
        assert len(group) == 8 and sum(r['first_form']=='A' for r in group)==4
        assert abs(sum(r['experience'] for r in group)*2 - experienced)<=1


def event(i, kind, **data):
    return {'id':i,'at_ms':i*100,'type':kind,'data':data}


def test_research_capture_summary_keeps_missing_onset_distinct_from_zero():
    events = [event(0, 'student', student_id='yu', reply_id='a', text='一半。'),
              event(0, 'playback_onset', reply_id='a'),
              event(2, 'playback', reply_id='a', status='playback_completed'),
              event(3, 'student', student_id='yu', reply_id='b', text='两块。'),
              event(4, 'playback', reply_id='b', status='playback_completed'),
              event(5, 'student', student_id='yu', reply_id='c', text='一份。')]
    evidence, _ = study_evidence(events, 'multimodal')
    summary = capture_summary(evidence)
    assert summary['completed_with_both_timestamps'] == 1
    assert summary['completed_without_onset'] == ['b']
    assert summary['completed_replies'] == 2 and summary['unconfirmed'] == 1
    assert summary['motion_samples']['hands'] == {'observed_samples': 0, 'total_samples': 0}
    assert set(study_evidence(events, 'transcript')[0]) == {'transcript'}


def test_shared_transcript_and_playback_gaps():
    events = [event(1,'transcript',text='这表示什么？',source='asr_final'),
              event(2,'student',student_id='lin',reply_id='a',text='一半。',study_step='conclusion'),
              event(3,'playback_onset',reply_id='a'),event(4,'playback',reply_id='a',status='playback_completed'),
              event(5,'student',student_id='yu',reply_id='b',text='未核实的理由'),
              event(6,'interrupt',reply_id='b'), event(7,'playback',reply_id='b',status='playback_completed')]
    t, anchors = study_evidence(events, 'transcript')
    m, _ = study_evidence(events, 'multimodal')
    assert set(t) == {'transcript'} and t['transcript'] == m['transcript']
    assert '未核实' not in str(m)
    assert anchors[-1]['at_ms']==300 and m['playback'][1]['status']=='interrupted_or_failed'
    assert student_cue('round1','lin','为什么',events)['step']=='basis'
    assert student_cue('round1','lin','为什么',events[:3])['step']=='conclusion'
    assert student_cue('round2','yu','你说',[])['step']=='reason'
    assert student_cue('round2','ming','你说',[])['step']=='stable'
    assert student_cue('round1','yu','这表示什么？',[])['step']=='challenge'
    assert m['teacher_motion']['status']=='insufficient'


def test_premature_explanation_is_withheld():
    assert constrain_line('conclusion','一半，因为两份一样大。')=='我觉得这一份是一半。'
    assert constrain_line('reason','我已经知道平均分了。')=='我数了两份，所以我觉得这一块就是一半。'
    assert constrain_line('compare','我可以把两份对折。')=='我可以把两份对折。'


@pytest.mark.parametrize('arm',['multimodal','transcript'])
def test_two_visits_on_real_api(app, tmp_path, arm):
    client = app.test_client()
    users = [User(account=f'study{i}',name='试跑',password_hash='unused') for i in range(2)]
    db.session.add_all(users);db.session.flush()
    tenant = personal_tenant_for(users[0])
    p=StudyParticipant(user_id=users[0].id,tenant_id=tenant.id,code='P01',experience=False,arm=arm,first_form='A')
    db.session.add(p);db.session.commit()
    auth=headers(users[0].id)
    def post(path,data):
        return client.post('/api/'+path,headers=auth,json=data)
    def get():
        return client.get('/api/study',headers=auth).json
    assert get()['arm'] is None
    assert post('study/attempts',{'stage':'round1','consent':True}).status_code==409
    clips=[]
    for stage in ('pre','round1','round2','post'):
        assert get()['stage']==stage
        args={'consent':True,'stage':stage}
        attempt=post('study/attempts',args).json
        aid=attempt['id']; base=f'study/attempts/{aid}'
        assert post('study/attempts',args).json['id']==aid
        if stage in ('pre','post'):
            clips.append(attempt['clip'])
            form={'marks':[8000,147000],'av_checked':True,'duration_ms':300000,'note':'','actor':'T01'}
            assert post(base+'/assessment',{**form,'marks':[8000]}).status_code==400
            assert post(base+'/assessment',form).status_code==200
            assert get()['arm']==arm
            continue
        room=post('classroom/sessions',{'study_attempt':aid,'camera_consent':True,'audio_consent':True,
                                        'mode':'fragment','cloud_vision':True}).json
        sid=room['session_id']
        assert room['mode']=='full' and not room['cloud_vision'] and room['study_stage']==stage
        assert room['study_arm']==arm
        assert client.get('/api/'+base+'/evidence',headers=headers(users[1].id)).status_code==404
        classroom=db.session.get(Classroom,sid)
        classroom.started_at=datetime.utcnow()-timedelta(minutes=10)
        db.session.add_all([
            ClassroomEvent(session_id=sid,event_key='one',kind='transcript',at_ms=2000,
                           payload={'text':'请看这两份。','source':'asr_final'}),
            ClassroomEvent(session_id=sid,event_key='two',kind='student',at_ms=2500,
                           payload={'student_id':'lin','name':'小林','reply_id':'a','text':'我觉得是一半。'}),
            ClassroomEvent(session_id=sid,event_key='three',kind='playback',at_ms=2600,
                           payload={'reply_id':'a','status':'playback_completed'}),
        ])
        db.session.commit()
        assert post(f'classroom/sessions/{sid}/finish',{}).status_code==202
        assert classroom.report is None
        assert post(f'classroom/sessions/{sid}/report',{}).status_code==409
        assert post(base+'/complete',{'reviewed_video':True,'goal':'先听理由'}).status_code==409
        assert post(base+'/reflection',{'text':'听听理由','at_ms':2000}).status_code==200
        row=db.session.get(StudyAttempt,aid)
        assert ('teacher_motion' in row.packet)==(arm=='multimodal')
        data=issue_document(aid, row.packet)
        file=tmp_path/f'{aid}.json'
        file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        runner=app.test_cli_runner()
        assert runner.invoke(args=['study','issue',str(aid),str(file)]).exit_code==0
        file.write_text(json.dumps({**data,'text':'覆盖'}))
        assert runner.invoke(args=['study','issue',str(aid),str(file)]).exit_code!=0
        evidence=client.get('/api/'+base+'/evidence',headers=auth).json
        assert evidence['turns'][0]['at_ms']==2000
        assert post(base+'/complete',{'reviewed_video':True,'goal':'先听理由'}).status_code==200
    assert get()['stage'] is None and clips[0]!=clips[1]
    assert app.test_cli_runner().invoke(args=['study','repeat',str(aid),'音轨受损；另行复测']).exit_code==0
    assert get()['stage']=='post' and get()['attempts'][-1]['previous_id']==aid


TEACHER_A = '请同学们看这张纸，我们把一整张平均分成两份，再看涂色的这一份可以怎样表示，先不要急着算。'
TEACHER_B = '你是怎样看出来的？两份是不是一样大？请你指一指，并说出判断的依据，请不要只去数一共有几块。'
STUDENT_LINE = '我觉得涂色的这一份是一半。'


def ready_events(interrupted=False):
    rows = [event(1,'transcript',text=TEACHER_A,source='asr_final'),
            event(2,'student',student_id='lin',name='小林',reply_id='a',text=STUDENT_LINE),
            event(3,'playback',reply_id='a',status='playback_completed'),
            event(4,'transcript',text=TEACHER_B,source='asr_final')]
    if interrupted:
        rows += [event(5,'student',student_id='yu',name='小宇',reply_id='b',text='未核实的理由'),
                 event(6,'interrupt',reply_id='b')]
    return rows


def seal(packet):
    user = User(account='review-gate', name='评', password_hash='unused')
    db.session.add(user)
    db.session.flush()
    tenant = personal_tenant_for(user)
    participant = StudyParticipant(user_id=user.id, tenant_id=tenant.id, code='P02',
                                   experience=False, arm='transcript', first_form='A')
    db.session.add(participant)
    db.session.flush()
    row = StudyAttempt(participant_id=participant.id, stage='round1', version='unit-fraction-1', packet=packet)
    db.session.add(row)
    db.session.commit()
    return row


def test_draft_transcript_never_enters_the_packet():
    events = ready_events() + [event(9,'transcript',text='这是还没定稿的一句')]
    packet, _ = study_evidence(events, 'transcript')
    assert '还没定稿' not in json.dumps(packet, ensure_ascii=False)
    assert [item['text'] for item in packet['transcript'] if item['speaker']=='教师'] == [TEACHER_A, TEACHER_B]


def test_review_request_is_shared_and_transcript_arm_has_no_motion(app, tmp_path, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_CHAT_MODEL', MODEL)
    monkeypatch.setattr('services.study_review.cache_dir', lambda: tmp_path)
    events = ready_events(interrupted=True)
    transcript, _ = study_evidence(events, 'transcript')
    multimodal, _ = study_evidence(events, 'multimodal')
    assert transcript['transcript'] == multimodal['transcript']
    assert '未核实' not in json.dumps(transcript['transcript'], ensure_ascii=False)
    calls = []

    def fake(packet):
        calls.append(packet)
        from services.study_review import fixture_body
        episodes, nxt = fixture_body(packet)
        return {'episodes': episodes, 'next_try': nxt}

    monkeypatch.setattr('services.study_review.complete_model', fake)
    first = compile_review(7, transcript)
    second = compile_review(8, transcript)
    assert len(calls) == 1 and calls[0] == transcript
    assert second['text'] == first['text'] and second['sha256'] == first['sha256']
    assert first['request']['system'] == SYSTEM and set(first['request']['user']) == {'transcript'}
    sent = user_content(first['request']['user'])
    assert 'playback' not in sent and 'teacher_motion' not in sent and 'start_ms' not in sent
    multi = compile_review(9, multimodal)
    assert multi['request']['system'] == first['request']['system']
    assert 'playback' in multi['request']['user'] and 'teacher_motion' in multi['request']['user']
    assert len(calls) == 2
    blamed = issue_document(1, multimodal)
    blamed['episodes'][0]['fact'] += '教师忽略了学生没有说完的理由。'
    blamed['text'] = render(blamed['episodes'], blamed['next_try'])
    with pytest.raises(ValueError, match='忽略'):
        validate_issue(multimodal, blamed)
    forged = issue_document(1, transcript)
    forged['episodes'][0]['student_quote'] = '没说过这句话'
    forged['text'] = render(forged['episodes'], forged['next_try'])
    with pytest.raises(ValueError, match='连续子串'):
        validate_issue(transcript, forged)
    leaked = json.loads(json.dumps(transcript))
    leaked['transcript'][0]['start_ms'] = 15
    with pytest.raises(ValueError, match='播放、动作或毫秒'):
        issue_document(1, leaked)
    changed = issue_document(1, transcript)
    changed['rubric_version'] = 'other'
    with pytest.raises(ValueError, match='冻结规格'):
        validate_issue(transcript, changed)


def test_generate_refuses_unfinished_recognition_and_a_different_model(app, tmp_path, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_CHAT_MODEL', MODEL)
    monkeypatch.setattr('services.study_review.cache_dir', lambda: tmp_path)
    called = []
    monkeypatch.setattr('services.study_review.complete_model', lambda packet: called.append(packet))
    packet, _ = study_evidence([event(1,'transcript',text='请看这两份。',source='asr_final')], 'transcript')
    row = seal(packet)
    output = tmp_path/'report.json'
    result = app.test_cli_runner().invoke(args=['study','generate',str(row.id),str(output)])
    assert result.exit_code != 0 and '识别未完成' in result.output and not output.exists() and called == []
    monkeypatch.setenv('DEEPSEEK_CHAT_MODEL', 'other-model')
    ready, _ = study_evidence(ready_events(), 'transcript')
    with pytest.raises(ValueError, match=MODEL):
        compile_review(row.id, ready)


def test_speech_probe_names_the_recognizer_endpoint(app, monkeypatch):
    def fail():
        raise ProviderError('连接中断')
    monkeypatch.setattr('services.classroom_speech.probe_asr', fail)
    failed = app.test_cli_runner().invoke(args=['study','speech-probe'])
    assert failed.exit_code != 0 and 'wss://iat.xf-yun.com/v1' in failed.output
    monkeypatch.setattr('services.classroom_speech.probe_asr', lambda: None)
    assert app.test_cli_runner().invoke(args=['study','speech-probe']).exit_code == 0


def test_model_request_sends_only_the_packet(app, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_CHAT_MODEL', MODEL)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-key')
    monkeypatch.setenv('AI_LLM_INPUT_CNY_PER_MILLION', '1')
    monkeypatch.setenv('AI_LLM_OUTPUT_CNY_PER_MILLION', '1')
    packet, _ = study_evidence(ready_events(), 'transcript')
    calls = []

    class Response:
        status_code = 200
        def json(self):
            return {'choices': [{'message': {'content': '{"episodes":[]}'}}],
                    'usage': {'prompt_tokens': 3, 'completion_tokens': 4}}

    def post(url, **kwargs):
        calls.append(kwargs)
        return Response()

    monkeypatch.setattr('services.study_review.httpx.post', post)
    from services.study_review import complete_model
    assert complete_model(packet) == {'episodes': []}
    body = calls[0]['json']
    assert body['temperature'] == TEMPERATURE and body['top_p'] == 1
    assert body['thinking'] == {'type': 'disabled'} and body['max_tokens'] == 1200
    assert body['messages'] == [{'role': 'system', 'content': SYSTEM},
                                {'role': 'user', 'content': user_content(packet)}]
    assert calls[0]['headers']['Authorization'] == 'Bearer synthetic-key'
    assert 'playback' not in body['messages'][1]['content']
