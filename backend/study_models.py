"""The participant key and blind clip key have separate audiences."""
import uuid
from datetime import datetime

from extensions import db


class StudyParticipant(db.Model):
    __tablename__ = 'study_participants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    code = db.Column(db.String(8), nullable=False)
    experience = db.Column(db.Boolean, nullable=False)
    arm = db.Column(db.String(16), nullable=False)
    first_form = db.Column(db.String(1), nullable=False)
    __table_args__ = (db.UniqueConstraint('tenant_id', 'user_id'), db.UniqueConstraint('tenant_id', 'code'))


class StudyAttempt(db.Model):
    __tablename__ = 'study_attempts'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('study_participants.id'), nullable=False)
    stage = db.Column(db.String(12), nullable=False)
    number = db.Column(db.Integer, nullable=False, default=1)
    previous_id = db.Column(db.Integer, db.ForeignKey('study_attempts.id'))
    clip = db.Column(db.String(32), nullable=False, unique=True, default=lambda: uuid.uuid4().hex)
    session_id = db.Column(db.Integer, db.ForeignKey('classrooms.session_id'), unique=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished = db.Column(db.DateTime)
    version = db.Column(db.String(40), nullable=False)
    assessment = db.Column(db.JSON)
    reflection = db.Column(db.JSON)
    packet = db.Column(db.JSON)
    issued = db.Column(db.JSON)
    goal = db.Column(db.Text)
    anomaly = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint('participant_id', 'stage', 'number'),)
