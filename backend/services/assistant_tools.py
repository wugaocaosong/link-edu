import json
import re
from datetime import datetime
from pathlib import Path

from extensions import db
from services.assistant_interview import InterviewPlan, bank
from tenancy import Tenant, TenantMembership


class AssistantMistake(db.Model):
    __tablename__ = 'assistant_mistakes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    question_key = db.Column(db.String(64), nullable=False)
    question = db.Column(db.String(600), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'tenant_id', 'question_key'),)


class AssistantToolAudit(db.Model):
    __tablename__ = 'assistant_tool_audit'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    tool = db.Column(db.String(32), nullable=False)
    outcome = db.Column(db.String(24), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def allowed_workspace(uid, tenant_id):
    return tenant_id is not None and TenantMembership.query.join(Tenant).filter(
        TenantMembership.user_id == uid, TenantMembership.tenant_id == tenant_id,
        TenantMembership.status == 'active', Tenant.status == 'active').first() is not None


def audit(uid, tenant_id, name, outcome):
    db.session.add(AssistantToolAudit(user_id=uid, tenant_id=tenant_id, tool=name, outcome=outcome))


CATALOG = json.loads((Path(__file__).resolve().parents[1] / 'data/assistant-resources.json').read_text(encoding='utf-8'))


def tool_intent(text):
    text = text.strip().rstrip('。！!？?')
    if match := re.fullmatch(r'(?:请|帮我|请帮我)?打开\s*(.{1,100})', text):
        return 'open_resource', {'query': match[1].strip('《》「」 ')}
    if re.fullmatch(r'(?:请|帮我|请帮我)?(?:(?:把|将)?(?:(?:刚才|刚刚|当前|上)(?:的)?(?:这|那|一)?(?:道)?题|[这那]道题).{0,12}(?:错题本|错题库)|加入错题本)', text):
        return 'add_mistake', {}
    if re.fullmatch(r'(?:请|帮我|请帮我)?(?:生成|制定|创建|更新|调整).{0,14}(?:备考计划|复习计划)', text):
        return 'make_plan', {}
    if re.fullmatch(r'(?:请|帮我|请帮我)?(?:总结|概括|归纳)(?:一下)?(?:当前|本页|这份|这篇).{0,20}', text):
        return 'summarize_page', {}
    if re.fullmatch(r'(?:请|帮我|请帮我)?(?:给我出|出|来)(?:一|下)?(?:道)?题|考考我|今天练什么|继续练习', text):
        return 'quiz_me', {}
    return None


def find_resource(query):
    term = ''.join(query.lower().split())
    if not term:
        return None

    def rank(item):
        title = ''.join(item['title'].lower().split())
        category = ''.join(item['category'].lower().split())
        if term in (title, category):
            return 3
        if term in title or term in category:
            return 2
        if term == '结构化真题' and category == '历年真题':
            return 1
        return 0
    best = max(CATALOG, key=rank, default=None)
    return best if best and rank(best) else None


def select_quiz(profile, previous):
    questions = list(bank().values())
    return next((item for item in questions if item['id'] != previous and item['topic'] in profile['weaknesses']),
                next((item for item in questions if item['id'] != previous), None))


def prepare_plan(uid, tenant_id, operation):
    if operation != 'update':
        return None
    return InterviewPlan.query.filter_by(user_id=uid, tenant_id=tenant_id, kind='week').order_by(
        InterviewPlan.id.desc()).first()
