"""Opt-in adaptive learning tables. No migrations or seed writes on import."""
from datetime import datetime
from extensions import db


class Skill(db.Model):
    __tablename__ = 'adaptive_skills'
    id = db.Column(db.String(24), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ordinal = db.Column(db.Integer, nullable=False, unique=True)


class SkillMaterial(db.Model):
    __tablename__ = 'adaptive_skill_materials'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.String(24), db.ForeignKey('adaptive_skills.id'), nullable=False, index=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('skill_id', 'level'), db.CheckConstraint('level BETWEEN 1 AND 3'))


class Question(db.Model):
    __tablename__ = 'adaptive_questions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(48), nullable=False, unique=True)
    skill_id = db.Column(db.String(24), db.ForeignKey('adaptive_skills.id'), nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (db.CheckConstraint('level BETWEEN 1 AND 3'),)


class Quiz(db.Model):
    __tablename__ = 'adaptive_quizzes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    request_key = db.Column(db.String(64), nullable=False)
    skill_id = db.Column(db.String(24), db.ForeignKey('adaptive_skills.id'))
    status = db.Column(db.String(16), nullable=False, default='open')
    scores = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('user_id', 'request_key'),)


class Answer(db.Model):
    __tablename__ = 'adaptive_answers'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('adaptive_quizzes.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('adaptive_questions.id'), nullable=False)
    ordinal = db.Column(db.Integer, nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)
    selected = db.Column(db.String(1))
    correct = db.Column(db.Boolean)
    __table_args__ = (db.UniqueConstraint('quiz_id', 'question_id'), db.UniqueConstraint('quiz_id', 'ordinal'))


class Mastery(db.Model):
    __tablename__ = 'adaptive_mastery'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    skill_id = db.Column(db.String(24), db.ForeignKey('adaptive_skills.id'), primary_key=True)
    quiz_score = db.Column(db.Float)
    training_score = db.Column(db.Float)
    score = db.Column(db.Float)
    evidence = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (db.CheckConstraint('score IS NULL OR (score >= 0 AND score <= 100)'),)


class LearningPath(db.Model):
    __tablename__ = 'adaptive_paths'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fingerprint = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'fingerprint'),)


class PathStep(db.Model):
    __tablename__ = 'adaptive_path_steps'
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey('adaptive_paths.id'), nullable=False, index=True)
    skill_id = db.Column(db.String(24), db.ForeignKey('adaptive_skills.id'), nullable=False)
    ordinal = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    reason = db.Column(db.JSON, nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('adaptive_skill_materials.id'))
    practice_plan_id = db.Column(db.Integer, db.ForeignKey('classroom_practice_plans.id'))
    status = db.Column(db.String(16), nullable=False, default='pending')
    __table_args__ = (db.UniqueConstraint('path_id', 'ordinal'),)


class LearningProgress(db.Model):
    __tablename__ = 'adaptive_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    step_id = db.Column(db.Integer, db.ForeignKey('adaptive_path_steps.id'), nullable=False, unique=True)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
