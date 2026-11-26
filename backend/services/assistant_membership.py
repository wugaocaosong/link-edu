from extensions import db


class AssistantMembership(db.Model):
    __tablename__ = 'assistant_memberships'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    plus_until = db.Column(db.DateTime)
    last_check_in = db.Column(db.Date)


class AssistantPointEntry(db.Model):
    __tablename__ = 'assistant_point_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


def prototype_membership():
    return {'tier': 'free', 'advanced_locked': True, 'payments_enabled': False}
