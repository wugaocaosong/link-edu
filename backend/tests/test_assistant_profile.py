from flask_jwt_extended import create_access_token
from test_classroom_base import app

import assistant_routes as routes
from extensions import db
from models import User
from services.assistant_profile import learning_signals, read_profile, update_profile
from services.classroom_stream import StreamControl
from test_assistant import Wire, session


def test_profile_survives_disconnect_and_is_scoped_to_jwt_user(app, monkeypatch):
    first = User(account='profile-a', name='A', password_hash='synthetic')
    second = User(account='profile-b', name='B', password_hash='synthetic')
    db.session.add_all([first, second])
    db.session.commit()
    first_uid, second_uid = first.id, second.id
    live = routes.AssistantSession(app, Wire(), first_uid, 'text')
    monkeypatch.setattr(live, 'answer', lambda *args: None)
    live.submit('我结构化总卡在人际关系题')
    live.close()

    wire = Wire()
    reopened = routes.AssistantSession(app, wire, first_uid, 'text')
    assert reopened.profile['weaknesses'] == ['人际关系']
    assert routes.AssistantSession(app, Wire(), second_uid, 'text').profile['weaknesses'] == []
    monkeypatch.setattr('rag.service.report_reference_sources', lambda *args, **kwargs: [])
    reopened.turn = 'practice'
    reopened.generations.acquire()
    reopened.answer('practice', '今天练什么', StreamControl())
    assert '原创模拟题' in next(message['text'] for message in wire.messages if message['type'] == 'answer')

    assert update_profile(first_uid, {'preferences': ['先给提示', 'fake@example.test']})['preferences'] == ['先给提示']
    assert read_profile(first_uid)['weaknesses'] == ['人际关系']
    headers = {'Authorization': 'Bearer ' + create_access_token(identity=str(second_uid))}
    client = app.test_client()
    assert client.get(f'/api/assistant/profile?uid={first_uid}', headers=headers).json['weaknesses'] == []
    response = client.post('/api/assistant/profile/practice', headers=headers,
                           json={'uid': first_uid, 'topic': '家校沟通', 'consecutive_incomplete': 2})
    assert response.json['mistake_types'] == ['家校沟通']
    assert read_profile(first_uid)['mistake_types'] == []


def test_only_explicit_or_repeated_signals_create_labels():
    questions = {}
    assert not any(learning_signals('人际关系题怎么答？', questions).values())
    assert not any(learning_signals('人际关系题怎么答？', questions).values())
    assert learning_signals('人际关系题怎么练？', questions)['preferences'] == ['逐题练习']
    assert learning_signals('我的目标是通过教资面试', {})['goals'] == ['教资面试']
    assert not any(learning_signals('我不是总卡在人际关系题', {}).values())
    assert not any(learning_signals('不是我的情况：我总卡在人际关系题', {}).values())


def test_summary_is_cached_and_page_sources_are_citable(app, monkeypatch):
    owner, wire = session(app)
    owner.history = [{'role': 'user', 'content': str(index)} for index in range(14)]
    owner.page_sources = routes.page_references({'reportFull': '教学生成了两份作品', 'uid': 'ignored'})
    calls = []

    def stream(prompt, payload, *args):
        calls.append(payload)
        if prompt == routes.SUMMARY_PROMPT:
            return {'text': '此前用户讨论学习评价', 'source_ids': []}
        return {'text': '报告显示学生生成了两份作品。', 'source_ids': ['page:reportFull']}

    monkeypatch.setattr('rag.service.report_reference_sources', lambda *args, **kwargs: [])
    monkeypatch.setattr('services.assistant_dialogue.chat_stream', stream)
    for turn in ('one', 'two'):
        owner.turn = turn
        owner.generations.acquire()
        owner.answer(turn, '总结当前报告', StreamControl())
    assert len(calls) == 3
    assert len(calls[0]['older_dialogue']) == routes.SUMMARY_BATCH
    assert all(call['earlier_dialogue_summary'] == '此前用户讨论学习评价' for call in calls[1:])
    assert next(message for message in wire.messages if message['type'] == 'answer')['sources'][0]['id'] == 'page:reportFull'
