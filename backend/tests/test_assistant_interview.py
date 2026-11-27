import json
import sys
import unittest
import time
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask_jwt_extended import create_access_token
from app import create_app
from assistant_routes import AssistantSession, COMMON_LABEL, DEPTHS, classify_answer
from extensions import db
from classroom_models import ApiUsage, CreditUsage
from models import AiFeedback, User
from services.assistant_interview import bank
from services.assistant_dialogue import attachment_reference, chat_with_tool, lesson_plan_sections, parse_tool_call
from services.assistant_tools import AssistantMistake, AssistantToolAudit, find_resource, tool_intent
from services.assistant_quota import receipt
from services.classroom_stream import StreamControl
from tenancy import personal_tenant_for


class Config:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    JWT_SECRET_KEY = 'test-key-long-enough-for-jwt-signing'


class Wire:
    def __init__(self):
        self.messages = []

    def send(self, raw):
        self.messages.append(json.loads(raw))


class AssistantInterviewTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        db.create_all()
        self.user = User(account='assistant-practice', name='test', password_hash='not-a-real-hash')
        self.other = User(account='assistant-other', name='other', password_hash='not-a-real-hash')
        db.session.add_all([self.user, self.other])
        db.session.flush()
        tenant = personal_tenant_for(self.user, commit=True)
        self.tenant_id = tenant.id
        self.wire = Wire()
        self.owner = AssistantSession(self.app, self.wire, self.user.id, 'text', tenant_id=tenant.id)

    def run_action(self, control=None, **data):
        control = control or StreamControl()
        self.owner.turn = 'turn'
        self.owner.generations.acquire()
        self.owner.run_interview('turn', control, 'request', data)
        return self.wire.messages[-1]

    def test_real_question_and_validated_rubric(self):
        def model(prompt, payload, control, draft, *args, validator):
            if 'candidates' in payload:
                self.assertTrue(all(item['id'] in bank() for item in payload['candidates']))
                return validator({'question_id': payload['candidates'][0]['id']})
            draft('简短反馈')
            return validator({'text': '建议细化理由', 'missing': [2],
                              'dimensions': {key: {'score': 73, 'advice': '补一个具体动作'}
                                             for key in ('content', 'structure', 'language')}})

        with patch('services.assistant_interview.chat_stream', side_effect=model):
            question = self.run_action(action='question', mode='structured', topic='人际关系')['result']
            self.assertNotIn('points', question)
            response = self.run_action(action='grade', mode='structured', question_id=question['id'], answer='我会先沟通。')
        result = response['result']
        self.assertEqual(result['dimensions']['content']['score'], 67)
        self.assertEqual(set(result['dimensions']), {'content', 'structure', 'language', 'time'})
        self.assertEqual(result['citation']['number'], bank()[question['id']]['number'])
        self.assertTrue(any(event['type'] == 'interview_delta' for event in self.wire.messages))

    def test_tool_decision_is_bounded_and_result_is_returned_to_model(self):
        name, defaults = tool_intent('打开结构化真题')
        self.assertEqual(name, 'open_resource')
        self.assertIn('真题', find_resource(defaults['query'])['title'])
        with self.assertRaises(ValueError):
            parse_tool_call({'tool_use': {'name': 'open_resource', 'arguments': {'query': '资料', 'url': 'invalid'}}}, name)
        with self.assertRaises(ValueError):
            parse_tool_call({'tool_use': {'name': 'make_plan', 'arguments': {}}}, name)
        calls = []

        def model(prompt, payload, *args, **kwargs):
            calls.append(payload)
            if len(calls) == 1:
                return kwargs['validator']({'tool_use': {'name': name, 'arguments': defaults}})
            return {'text': '已找到资料', 'source_ids': ['tool:open_resource']}

        with patch('services.assistant_dialogue.chat_stream', side_effect=model):
            reply, _ = chat_with_tool('system', {'question': '打开结构化真题'}, StreamControl(), self.user.id, name,
                                    lambda name, args: {'message': find_resource(args['query'])['title']}, defaults)
        self.assertEqual(reply['text'], '已找到资料')
        self.assertIn('tool_result', calls[1])

    def test_mistake_requires_confirmation_and_cannot_replay(self):
        control = StreamControl()
        self.owner.turn = 'turn'
        self.owner.control = control
        self.owner.current_question = {'id': 'test', 'question': '模拟题：如何向家长说明课程安排？'}
        result = self.owner.execute_tool('turn', control, 'add_mistake', {}, '把刚才那道题记进错题本', [])
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(AssistantMistake.query.count(), 0)
        card = self.wire.messages[-1]['card']
        self.owner.confirm_tool({'token': 'wrong', 'accepted': True})
        self.assertEqual(AssistantMistake.query.count(), 0)
        with patch('services.assistant_dialogue.answer_tool_result', return_value=({'text': '已记入'}, {})):
            self.owner.confirm_tool({'token': card['token'], 'accepted': True})
            self.owner.threads[-1].join(3)
            self.owner.confirm_tool({'token': card['token'], 'accepted': True})
        self.assertEqual(AssistantMistake.query.count(), 1)
        self.assertEqual([item.outcome for item in AssistantToolAudit.query.order_by(AssistantToolAudit.id)], ['pending', 'confirmed'])
        client = self.app.test_client()
        for uid, count in ((self.user.id, 1), (self.other.id, 0)):
            headers = {'Authorization': 'Bearer ' + create_access_token(identity=str(uid))}
            self.assertEqual(len(client.get('/api/assistant/mistakes', headers=headers).json['items']), count)

    def test_expired_confirmation_does_not_write(self):
        control = StreamControl()
        self.owner.turn = 'turn'
        self.owner.generations.acquire()
        self.owner.apply_tool('turn', control, time.monotonic()-1, 'add_mistake', {'question': '题目'}, True)
        self.assertEqual(AssistantMistake.query.count(), 0)
        self.assertEqual(AssistantToolAudit.query.one().outcome, 'expired')

    def test_board_transcription_and_lesson_plan_fields(self):
        attachment = SimpleNamespace(kind='image', ext='png', name='board.png', data=b'\x89PNG\r\n\x1a\n')
        with patch.dict('os.environ', {'TEST_VISION_KEY': 'test'}), \
             patch('services.assistant_dialogue.llm_provider', return_value='deepseek'), \
             patch('services.assistant_dialogue.deepseek_credential', return_value='TEST_VISION_KEY'), \
             patch('services.assistant_dialogue.model', return_value='deepseek-v4-flash-vision-exp'), \
             patch('services.classroom_providers.chat', return_value={
                 'text': '分数', 'layout': '左侧标题', 'observations': '画面右侧有一只举起的手'}) as vision:
            result = attachment_reference(attachment, StreamControl(), self.user.id)
        self.assertIn('板书转写：分数', result['text'])
        self.assertEqual(result['sections']['可见板书布局'], '左侧标题')
        self.assertEqual(vision.call_args.kwargs['user_id'], self.user.id)
        with patch('services.assistant_dialogue.chat_stream',
                   side_effect=lambda *args, validator: validator({
                       'objectives': '辨认分数', 'focus': '分数含义', 'difficulties': '', 'process': '先观察再表达'})):
            plan = lesson_plan_sections('教案摘录', StreamControl(), self.user.id)
        self.assertEqual(set(plan), {'教学目标', '教学重点', '教学过程'})

    def test_answer_tiers_keep_only_actual_sources(self):
        source = {'id': 'kb:lesson', 'title': '课堂教学资料'}
        draft = {'text': '先提出一个开放式问题。', 'source_ids': ['kb:lesson', 'invented'],
                 'answer_kind': 'common_teaching'}
        answer, cited, tier = classify_answer(draft, [source], '课堂提问怎么设计？')
        self.assertEqual((answer, cited, tier), (draft['text'], [source], 'grounded'))
        draft['source_ids'] = []
        answer, cited, tier = classify_answer(draft, [], '课堂提问怎么设计？')
        self.assertIn(COMMON_LABEL, answer)
        self.assertEqual((cited, tier), ([], 'common_teaching'))
        for question in ('猜猜明天的比分', '课堂提问的官方评分标准是什么？'):
            answer, cited, tier = classify_answer(draft, [], question)
            self.assertIn('我不知道', answer)
            self.assertEqual((cited, tier), ([], 'unknown'))
        draft['source_ids'] = ['invented']
        self.assertEqual(classify_answer(draft, [], '课堂提问怎么设计？')[2], 'unknown')

    def test_live_answer_adds_label_before_display_and_history(self):
        self.owner.turn = 'live'
        self.owner.depth = 'detailed'
        self.owner.generations.acquire()
        with patch('rag.service.report_reference_sources', return_value=[]), \
             patch('services.assistant_dialogue.chat_stream', return_value={
                 'text': '先提一个开放式问题。', 'source_ids': [], 'answer_kind': 'common_teaching'}) as model:
            self.owner.answer('live', '课堂提问怎么设计？', StreamControl())
        self.assertIn(DEPTHS['detailed'], model.call_args.args[0])
        answer = next(event for event in self.wire.messages if event['type'] == 'answer')
        self.assertEqual(answer['tier'], 'common_teaching')
        self.assertIn(COMMON_LABEL, answer['text'])
        self.assertEqual(self.owner.history[-1]['content'], answer['text'])

    def test_reply_receipt_combines_calls_but_not_other_accounts_or_turns(self):
        db.session.add_all([
            ApiUsage(service='dialogue', assistant_user_id=self.user.id, assistant_turn='test-turn',
                     reserved_cny=.1, charged_cny=.03, state='settled'),
            CreditUsage(account='vision', service='vision', model='mock', assistant_user_id=self.user.id,
                        assistant_turn='test-turn', reserved_usd=.02),
            ApiUsage(service='dialogue', assistant_user_id=self.user.id, assistant_turn='older', reserved_cny=.05),
            ApiUsage(service='dialogue', assistant_user_id=self.other.id, assistant_turn='test-turn', reserved_cny=.9),
        ])
        db.session.commit()
        with patch.dict('os.environ', {'USD_CNY_BUDGET_RATE': '8'}):
            current = receipt(self.user.id, 'test-turn')
            self.assertEqual(current['charged_cny'], .03)
            self.assertEqual(current['pending_cny'], .16)
            self.assertEqual(current['remaining_cny'], 1.76)
            self.assertEqual(current['calls'], 2)
            headers = {'Authorization': 'Bearer ' + create_access_token(identity=str(self.user.id))}
            details = self.app.test_client().get('/api/assistant/usage', headers=headers).json
            self.assertEqual(len(details['items']), 3)
            self.assertEqual(sum(row['status'] == 'settled' for row in details['items']), 1)

    def test_registration_grants_once_and_advanced_is_locked(self):
        from services.assistant_quota import AssistantTrialGrant
        client = self.app.test_client()
        credentials = {'account':'trial-teacher','password':'test-only-secret','name':'Demo','role':'teacher'}
        result = client.post('/api/auth/register', json=credentials)
        self.assertEqual(result.status_code, 201)
        uid = result.json['user']['id']
        headers = {'Authorization': 'Bearer ' + create_access_token(identity=str(uid))}
        self.assertEqual(db.session.get(AssistantTrialGrant, uid).amount_cents, 200)
        self.assertEqual(client.post('/api/auth/register', json=credentials).status_code, 409)
        db.session.add(ApiUsage(service='dialogue', assistant_user_id=uid, reserved_cny=.3, charged_cny=.2))
        db.session.commit()
        for _ in range(2):
            self.assertEqual(client.post('/api/auth/login', json=credentials).status_code, 200)
            self.assertEqual(client.get('/api/assistant/quota', headers=headers).json['remaining_cny'], 1.8)
        self.assertTrue(client.get('/api/assistant/membership', headers=headers).json['advanced_locked'])
        self.assertEqual(client.post('/api/assistant/membership/check_in', headers=headers).status_code, 404)
        self.assertEqual(client.post('/api/assistant/membership/redeem', headers=headers).status_code, 404)

    def test_plan_reload_check_in_and_scope(self):
        own_report = AiFeedback(user_id=self.user.id, tenant_id=self.tenant_id, overall_score=68, suggestion='补充退出题')
        foreign_report = AiFeedback(user_id=self.other.id, tenant_id=self.tenant_id, overall_score=70, suggestion='不应发送')
        db.session.add_all([own_report, foreign_report])
        db.session.commit()

        def model(prompt, payload, control, draft, *args, validator):
            self.assertEqual(payload['report']['suggestion'], '补充退出题')
            count = 7 if '恰好 7 步' in prompt else 3
            return validator({'steps': [{'task': '完成专项练习', 'criterion': '复述两个步骤'}] * count})

        with patch('services.assistant_interview.chat_stream', side_effect=model) as mocked:
            rejected = self.run_action(action='plan', kind='report', report_id=foreign_report.id)
            self.assertEqual(rejected['type'], 'interview_error')
            mocked.assert_not_called()
            saved = self.run_action(action='plan', kind='week')['result']
            route = self.run_action(action='plan', kind='report', report_id=own_report.id)['result']
            self.assertEqual(len(route['steps']), 3)
            self.assertEqual(route['report_id'], own_report.id)
            cancelled = StreamControl()
            cancelled.cancel()
            self.run_action(cancelled, action='plan', kind='week')
        client = self.app.test_client()
        owner = {'Authorization': 'Bearer ' + create_access_token(identity=str(self.user.id))}
        other = {'Authorization': 'Bearer ' + create_access_token(identity=str(self.other.id))}
        path = f"/api/assistant/interview-plans/{saved['id']}/steps/1"
        self.assertEqual(client.patch(path, headers=owner, json={'done': True}).json['completed'], [1])
        plans = client.get('/api/assistant/interview-plans', headers=owner).json['plans']
        self.assertEqual(len(plans), 2)
        self.assertEqual(next(plan for plan in plans if plan['id'] == saved['id'])['completed'], [1])
        self.assertEqual(client.patch(path, headers=other, json={'done': True}).status_code, 404)


if __name__ == '__main__':
    unittest.main()
