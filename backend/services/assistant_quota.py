"""One introductory CNY allowance per account, charged only for assistant model calls."""
import math
import os

from sqlalchemy import func, select

from classroom_models import ApiUsage, CreditUsage
from extensions import db

ALLOWANCE = 2.0


class QuotaExceeded(ValueError):
    pass


def conversion_rate():
    rate = float(os.getenv('USD_CNY_BUDGET_RATE', '8'))
    if not math.isfinite(rate) or rate < 1:
        raise ValueError('美元额度换算配置无效')
    return rate


def remaining(connection, user_id):
    totals = []
    for model, charge, reserve in ((ApiUsage, ApiUsage.charged_cny, ApiUsage.reserved_cny),
                                  (CreditUsage, CreditUsage.charged_usd, CreditUsage.reserved_usd)):
        query = select(func.coalesce(func.sum(func.coalesce(charge, reserve)), 0))
        totals.append(float(connection.execute(query.where(model.assistant_user_id == user_id)).scalar()))
    return max(0, ALLOWANCE - totals[0] - totals[1] * conversion_rate())


def check(connection, user_id, amount, currency='CNY'):
    cost = amount * conversion_rate() if currency == 'USD' else amount
    if cost > remaining(connection, user_id):
        raise QuotaExceeded('阿贝在线问答剩余额度不足，可继续使用本地帮助和面试练习。')


def status(user_id):
    with db.engine.connect() as connection:
        return {'allowance_cny': ALLOWANCE, 'remaining_cny': round(remaining(connection, user_id), 4)}
