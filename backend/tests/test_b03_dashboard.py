import unittest
from unittest.mock import patch
from uuid import uuid4
from pathlib import Path
import sys
from datetime import datetime

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from services.board_mail import MailUnavailable
from config import Config
from extensions import db
from models import User
from services.dashboard import build_dashboard_overview
from flask_jwt_extended import create_access_token
from models import Course, TrainingSession
from werkzeug.security import generate_password_hash


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    JWT_SECRET_KEY = 'b03-test-secret'
    SEED_ON_STARTUP = False


class DashboardOverviewTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.user = User(
            account='b03-user',
            password_hash=generate_password_hash('password'),
            name='B03 测试用户',
            role='student',
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_empty_dashboard_does_not_return_demo_growth_scores(self):
        with self.app.test_request_context():
            overview = build_dashboard_overview(self.user)

        self.assertEqual(overview['growth_trajectory'], [])
        self.assertIsNone(overview['continue_training'])
        self.assertIsNone(overview['ai_feedback'])
        self.assertEqual(overview['weekly_training']['summaries'], [])

    def test_empty_dashboard_sparkline_contains_only_zero_counts(self):
        with self.app.test_request_context():
            overview = build_dashboard_overview(self.user)
        self.assertEqual(overview['weekly_training']['sparkline'], [0] * 7)

    def test_board_mail_failure_then_retry_creates_one_note(self):
        client = self.app.test_client()
        headers = {'Authorization': f'Bearer {create_access_token(identity=str(self.user.id))}'}
        payload = dict(request_id=str(uuid4()), topic='其他', author='测试', body='反馈')
        with patch('routes.send_board_mail', side_effect=MailUnavailable('offline')):
            self.assertEqual(client.post('/api/board-messages', json=payload, headers=headers).status_code, 503)
        self.assertEqual(client.get('/api/journals', headers=headers).json['items'], [])
        with patch('routes.send_board_mail') as send:
            for expected in (201, 200):
                self.assertEqual(client.post('/api/board-messages', json=payload, headers=headers).status_code, expected)
            send.assert_called_once_with('其他', '测试', '反馈')
        self.assertEqual(len(client.get('/api/journals', headers=headers).json['items']), 1)

    def test_journal_is_read_back_after_a_new_request(self):
        headers = {'Authorization': f'Bearer {create_access_token(identity=str(self.user.id))}'}
        payload = {'entry_date': '2026-09-09', 'body': 'Persistent journal'}
        saved = self.app.test_client().post('/api/journals', json=payload, headers=headers)
        self.assertEqual(saved.status_code, 201)
        saved_id = saved.get_json()['item']['id']
        self.ctx.pop()
        self.ctx = self.app.app_context()
        self.ctx.push()

        loaded = self.app.test_client().get('/api/dashboard/overview', headers=headers)
        self.assertEqual(loaded.status_code, 200)
        journals = loaded.get_json()['weekly_training']['journals']
        self.assertEqual(journals[0]['id'], saved_id)
        self.assertEqual(journals[0]['body'], payload['body'])

    def test_continue_training_uses_the_persisted_course(self):
        course = Course(title='Actual Course', category='Microteaching', is_active=True)
        db.session.add(course)
        db.session.flush()
        db.session.add(TrainingSession(
            user_id=self.user.id, course_id=course.id, status='in_progress',
            progress_percent=40, duration_minutes=8, last_trained_at=datetime.utcnow(),
        ))
        db.session.commit()
        with self.app.test_request_context():
            overview = build_dashboard_overview(self.user)
        self.assertEqual(overview['continue_training']['course_id'], course.id)
        self.assertEqual(overview['continue_training']['progress_percent'], 40)
        self.assertGreater(overview['weekly_training']['sparkline'][-1], 0)


if __name__ == '__main__':
    unittest.main()
