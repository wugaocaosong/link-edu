"""One introductory CNY allowance per account, charged only for assistant model calls."""
import math
import os

from sqlalchemy import event, func, select, union_all

from classroom_models import ApiUsage, CreditUsage
from extensions import db
from models import User

ALLOWANCE_CENTS = 200


class AssistantTrialGrant(db.Model):
    __tablename__ = 'assistant_trial_grants'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    amount_cents = db.Column(db.Integer, nullable=False)


@event.listens_for(User, 'after_insert')
def grant_on_registration(mapper, connection, user):
    connection.execute(AssistantTrialGrant.__table__.insert().values(
        user_id=user.id, amount_cents=ALLOWANCE_CENTS))


def allowance(connection, user_id):
    cents = connection.execute(select(AssistantTrialGrant.amount_cents)
                               .where(AssistantTrialGrant.user_id == user_id)).scalar_one_or_none()
    return (cents or 0) / 100


class QuotaExceeded(ValueError):
    pass


def conversion_rate():
    rate = float(os.getenv('USD_CNY_BUDGET_RATE', '8'))
    if not math.isfinite(rate) or rate < 1:
        raise ValueError('美元额度换算配置无效')
    return rate


def remaining(connection, user_id, granted=None):
    totals = []
    for model, charge, reserve in ((ApiUsage, ApiUsage.charged_cny, ApiUsage.reserved_cny),
                                  (CreditUsage, CreditUsage.charged_usd, CreditUsage.reserved_usd)):
        query = select(func.coalesce(func.sum(func.coalesce(charge, reserve)), 0))
        totals.append(float(connection.execute(query.where(model.assistant_user_id == user_id)).scalar()))
    limit = allowance(connection, user_id) if granted is None else granted
    return max(0, limit - totals[0] - totals[1] * conversion_rate())


def check(connection, user_id, amount, currency='CNY'):
    cost = amount * conversion_rate() if currency == 'USD' else amount
    if cost > remaining(connection, user_id):
        raise QuotaExceeded('阿贝在线问答剩余额度不足，可继续使用本地帮助和面试练习。')


def status(user_id):
    with db.engine.connect() as connection:
        return balance(connection, user_id)


def balance(connection, user_id):
    granted = allowance(connection, user_id)
    return {'allowance_cny': granted, 'remaining_cny': round(remaining(connection, user_id, granted), 6)}


def usage_query(user_id, turn=None):
    sources = []
    for table, reserved, charged, rate in (
            (ApiUsage, ApiUsage.reserved_cny, ApiUsage.charged_cny, 1),
            (CreditUsage, CreditUsage.reserved_usd, CreditUsage.charged_usd, conversion_rate())):
        query = select(table.id, table.service, table.created_at, table.assistant_turn,
                       (reserved * rate).label('reserved'), (charged * rate).label('charged')).where(
                           table.assistant_user_id == user_id)
        if turn is not None:
            query = query.where(table.assistant_turn == turn)
        sources.append(query)
    return union_all(*sources).subquery()


def receipt(user_id, turn):
    usage = usage_query(user_id, turn)
    with db.engine.connect() as connection:
        rows = connection.execute(select(usage.c.charged, usage.c.reserved)).all()
        return {**balance(connection, user_id),
                'charged_cny': round(sum(row.charged or 0 for row in rows), 6),
                'pending_cny': round(sum(row.reserved for row in rows if row.charged is None), 6),
                'calls': len(rows)}


def history(user_id, page):
    usage = usage_query(user_id)
    rows_query = select(usage).order_by(usage.c.created_at.desc(), usage.c.id.desc(), usage.c.service).offset(page * 25).limit(26)
    with db.engine.connect() as connection:
        rows = connection.execute(rows_query).all()
        return {**balance(connection, user_id), 'has_more': len(rows) > 25,
                'items': [{'service': row.service, 'turn': row.assistant_turn,
                           'at': row.created_at.isoformat()+'Z',
                           'status': 'pending' if row.charged is None else 'settled',
                           'amount_cny': round(row.reserved if row.charged is None else row.charged, 6)}
                          for row in rows[:25]]}
