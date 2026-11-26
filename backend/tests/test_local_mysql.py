from unittest.mock import MagicMock

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from services import local_mysql


@pytest.mark.parametrize(('url', 'code', 'public'), [
    ('mysql+pymysql://localhost:3307/link', 1049, True),
    ('mysql+pymysql://database.example/link', 1049, False),
    ('mysql+pymysql://localhost:3307/link', 1045, False),
    ('mysql+pymysql://localhost:3307/link', 1044, False),
    ('mysql+pymysql://localhost:3307/link', 2003, False),
])
def test_only_missing_local_schema_can_trigger_creation(monkeypatch, url, code, public):
    engine = MagicMock(url=make_url(url))
    failure = OperationalError(None, None, Exception(code, 'connection failed'))
    monkeypatch.setattr(local_mysql, 'inspect', MagicMock(side_effect=failure))
    create = MagicMock()
    monkeypatch.setattr(local_mysql, 'create_engine', create)
    with pytest.raises(OperationalError) as caught:
        local_mysql.inspect_startup_tables(engine, public_deployment=public)
    assert caught.value is failure
    create.assert_not_called()
