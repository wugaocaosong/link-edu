"""Isolated Lab 5 database setup, SQL export and backend launcher. No original DB imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'lab5'
RUNTIME = OUT / 'runtime'
URL = 'mysql+pymysql://link_lab5:lab5-local-only@127.0.0.1:13316/link_lab5?charset=utf8mb4'


def protect():
    """Record hashes without opening a database connection."""
    paths = [ROOT / 'backend/.env', *list((ROOT / 'backend').glob('*.db')), *list((ROOT / 'backend/instance').glob('*.db'))]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def configure():
    os.environ.update(DATABASE_URL=URL, ADAPTIVE_ENABLED='true', SEED_ON_STARTUP='false',
                      PYTHON_DOTENV_DISABLED='1', PUBLIC_DEPLOYMENT='false',
                      JWT_SECRET_KEY='lab5-isolated-local-demo-secret-2026-only-0001',
                      LINK_RUNTIME_DIRECTORY=str(RUNTIME / 'locks'))
    # Never pass supplier keys to the experimental server.
    for key in list(os.environ):
        if any(word in key for word in ('API_KEY', 'API_SECRET', 'APP_SECRET')):
            os.environ.pop(key)
    sys.path.insert(0, str(ROOT / 'backend'))


def app_and_db(uri=URL):
    configure()
    from app import create_app
    from config import Config
    import adaptive_models
    from extensions import db
    class LabConfig(Config):
        SQLALCHEMY_DATABASE_URI = uri
        ADAPTIVE_ENABLED = True
        SEED_ON_STARTUP = False
        TESTING = True
    return create_app(LabConfig), db


def export_sql():
    from sqlalchemy.schema import CreateTable, CreateIndex
    from sqlalchemy.dialects import mysql
    app, db = app_and_db('sqlite://')
    folder = ROOT / 'backend/sql/lab5'
    folder.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db.create_all()
        from services.adaptive_catalog import seed_catalog
        seed_catalog()
        db.session.commit()
        dialect = mysql.dialect()
        ddl = ['-- Lab5 ONLY. Run with the restricted link_lab5 account.', 'USE link_lab5;', 'SET NAMES utf8mb4;']
        for table in db.metadata.sorted_tables:
            table_ddl = str(CreateTable(table, if_not_exists=True).compile(dialect=dialect)).strip()
            index_ddl = []
            for index in sorted(table.indexes, key=lambda i:i.name):
                columns = ', '.join('`'+c.name+'`' for c in index.columns)
                index_ddl.append(('UNIQUE ' if index.unique else '') + f'INDEX `{index.name}` ({columns})')
            if index_ddl:
                table_ddl = table_ddl[:-1].rstrip() + ',\n  ' + ',\n  '.join(index_ddl) + '\n)'
            ddl.append(table_ddl + ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
        (folder/'01_schema.sql').write_text('\n\n'.join(ddl)+'\n', encoding='utf-8')
        def literal(value):
            if value is None: return 'NULL'
            if isinstance(value, bool): return '1' if value else '0'
            if isinstance(value, (int, float)): return str(value)
            if isinstance(value, (dict, list)): value = json.dumps(value, ensure_ascii=False)
            if hasattr(value, 'isoformat'): value = value.isoformat(sep=' ')
            return "'" + str(value).replace('\\', '\\\\').replace("'", "''") + "'"
        seed = ['-- Synthetic accounts and original learning cards only.', 'USE link_lab5;', 'SET NAMES utf8mb4;', 'START TRANSACTION;']
        for table in db.metadata.sorted_tables:
            for row in db.session.execute(table.select()).mappings():
                cols = ', '.join('`'+k+'`' for k in row)
                pk = list(table.primary_key.columns)[0].name
                seed.append(f"INSERT INTO `{table.name}` ({cols}) VALUES ({', '.join(literal(v) for v in row.values())}) ON DUPLICATE KEY UPDATE `{pk}`=`{pk}`;")
        seed.append('COMMIT;')
        (folder/'02_seed.sql').write_text('\n\n'.join(seed)+'\n', encoding='utf-8')
        dictionary = {t.name:[dict(name=c.name,type=str(c.type),nullable=c.nullable,primary_key=c.primary_key,
                          references=[str(f.target_fullname) for f in c.foreign_keys]) for c in t.columns] for t in db.metadata.sorted_tables}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/'data-dictionary.json').write_text(json.dumps(dictionary, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Exported ORM-aligned schema and synthetic seed SQL.')


def setup():
    import pymysql
    from sqlalchemy.engine import make_url
    target = make_url(URL)
    if (target.host, target.port, target.database, target.username) != ('127.0.0.1', 13316, 'link_lab5', 'link_lab5'):
        raise RuntimeError('Refusing a non-lab target')
    before = protect()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'original-files-before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    connection = pymysql.connect(host=target.host,port=target.port,user=target.username,password=target.password,database=target.database,charset='utf8mb4')
    logs = []
    import sqlparse
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT VERSION(), DATABASE(), CURRENT_USER()')
            logs.append(str(cursor.fetchone()))
            for filename in ('01_schema.sql','02_seed.sql','03_verify.sql'):
                script = (ROOT/'backend/sql/lab5'/filename).read_text(encoding='utf-8')
                count = 0
                for statement in sqlparse.split(script):
                    try:
                        cursor.execute(statement)
                    except pymysql.err.OperationalError as error:
                        if error.args[0] == 1061 and statement.lstrip().startswith('CREATE INDEX'):
                            continue
                        raise
                    count += 1
                    if cursor.description:
                        logs.append(statement + '\n' + str(cursor.fetchall()))
                connection.commit()
                logs.append(f'{filename}: {count} statements completed')
    finally:
        connection.close()
    after = protect()
    (OUT/'original-files-after.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
    if before != after:
        raise RuntimeError('Original files changed during setup; inspect before continuing')
    logs.append('Original database and .env hashes unchanged: PASS')
    (OUT/'sql-execution.txt').write_text('\n\n'.join(logs), encoding='utf-8')
    print('\n'.join(logs[-5:]))


def serve():
    configure()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',5015))
    # Hardcoded evidence paths in legacy services are isolated by a source-only runtime copy.
    dest = RUNTIME / 'backend'
    for source in (ROOT/'backend').rglob('*'):
        rel = source.relative_to(ROOT/'backend')
        if any(part in {'.venv', '.venv-local', '__pycache__', '.pytest_cache', 'private', 'instance', 'tests'} for part in rel.parts):
            continue
        if source.is_file() and source.suffix in ('.py', '.json', '.md'):
            target = dest/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source,target)
    sys.path.insert(0,str(dest))
    from app import app
    # No init_db: the reviewed SQL is the only database initialization path.
    app.run(host='127.0.0.1',port=5015,debug=False,threaded=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['export','setup','serve'])
    args=parser.parse_args()
    {'export':export_sql,'setup':setup,'serve':serve}[args.action]()
