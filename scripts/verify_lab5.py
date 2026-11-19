"""Live MySQL acceptance and read-only evidence export. Uses only the restricted lab account."""
import concurrent.futures
import html
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import requests
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from lab5 import ROOT, OUT, app_and_db, protect

app, db = app_and_db()
results=[]
def check(name, condition):
    assert condition, name
    results.append({'test':name,'result':'PASS'})

with app.app_context():
    inspector=inspect(db.engine)
    for table in db.metadata.sorted_tables:
        expected={c.name for c in table.columns}
        actual={c['name'] for c in inspector.get_columns(table.name)}
        check('ORM columns: '+table.name, expected==actual)
    with db.engine.connect() as conn:
        tx=conn.begin()
        conn.execute(text("INSERT INTO adaptive_skills (id,name,description,ordinal) VALUES ('rollback_probe','事务回滚检查','合成验证',999)"))
        tx.rollback()
        check('transaction rollback', conn.execute(text("SELECT COUNT(*) FROM adaptive_skills WHERE id='rollback_probe'")).scalar()==0)
        conn.rollback()
        for name, sql in [
          ('foreign key rejection', "INSERT INTO adaptive_questions (code,skill_id,level,prompt,options,answer,explanation,active) VALUES ('fk-probe','missing',1,'x','{}','A','x',1)"),
          ('unique constraint rejection', "INSERT INTO adaptive_skills (id,name,description,ordinal) VALUES ('pace','duplicate','x',999)"),
          ('check constraint rejection', "INSERT INTO adaptive_questions (code,skill_id,level,prompt,options,answer,explanation,active) VALUES ('check-probe','pace',7,'x','{}','A','x',1)")]:
            try:
                conn.execute(text(sql))
            except Exception as error:
                check(name, any(code in str(error) for code in ('1452','1062','3819')))
            else:
                raise AssertionError(name+' was not enforced')
            finally:
                conn.rollback()
        check('Chinese round trip', conn.execute(text("SELECT name FROM adaptive_skills WHERE id='pace'")).scalar()=='教学节奏')
    # Concurrent HTTP replay validates the actual MySQL row-lock implementation.
    base='http://127.0.0.1:5015/api'
    login=requests.post(base+'/auth/login',json={'account':'lab5_peer','password':'Lab5-demo-2026'},timeout=10)
    login.raise_for_status()
    headers={'Authorization':'Bearer '+login.json()['access_token']}
    key='concurrent-audit-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    def create(_):
        r=requests.post(base+'/adaptive/quizzes',headers=headers,json={'request_key':key,'skill_id':'pace'},timeout=20)
        r.raise_for_status();return r.json()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        quizzes=list(pool.map(create,range(2)))
    check('concurrent create is idempotent',quizzes[0]['id']==quizzes[1]['id'])
    quiz=quizzes[0]
    answers={str(q['id']):'A' for q in quiz['questions']}
    def submit(_):
        r=requests.post(base+f"/adaptive/quizzes/{quiz['id']}/submit",headers=headers,json={'answers':answers},timeout=20)
        r.raise_for_status();return r.json()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        submitted=list(pool.map(submit,range(2)))
    check('concurrent submit returns same result', submitted[0]==submitted[1])
    def path(_):
        r=requests.post(base+'/adaptive/paths',headers=headers,json={},timeout=20)
        r.raise_for_status();return r.json()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        paths=list(pool.map(path,range(2)))
    check('concurrent path generation is idempotent',paths[0]['id']==paths[1]['id'])
    queries=[
      ('安装与连接', 'SELECT VERSION() AS MySQL版本, DATABASE() AS 数据库, CURRENT_USER() AS 实验账号'),
      ('数据库表清单', 'SELECT TABLE_NAME AS 表名, ENGINE AS 引擎 FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME'),
      ('题库与技能', 'SELECT s.name AS 技能, COUNT(q.id) AS 题目数, MIN(q.level) AS 最低难度, MAX(q.level) AS 最高难度 FROM adaptive_skills s JOIN adaptive_questions q ON q.skill_id=s.id GROUP BY s.id,s.name ORDER BY s.ordinal'),
      ('答题表字段', 'SHOW FULL COLUMNS FROM adaptive_answers'),
      ('掌握度与依据（合成实验账号）', 'SELECT u.account AS 账号,s.name AS 技能,m.quiz_score AS 测验分,m.training_score AS 训练分,m.score AS 掌握度 FROM adaptive_mastery m JOIN users u ON u.id=m.user_id JOIN adaptive_skills s ON s.id=m.skill_id ORDER BY u.id,s.ordinal'),
      ('关系约束', "SELECT TABLE_NAME AS 子表,COLUMN_NAME AS 外键,REFERENCED_TABLE_NAME AS 父表 FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL AND TABLE_NAME LIKE 'adaptive_%' ORDER BY TABLE_NAME"),
    ]
    evidence=[]
    with db.engine.connect() as conn:
        for title, query in queries:
            cursor=conn.execute(text(query))
            evidence.append({'title':title,'query':query,'columns':list(cursor.keys()),'rows':[list(row) for row in cursor.fetchall()]})

before=json.loads((OUT/'original-files-before.json').read_text(encoding='utf-8'))
check('Original database and .env hashes unchanged',before==protect())
(OUT/'mysql-acceptance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'mysql-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
css='body{font-family:"Microsoft YaHei",sans-serif;background:#edf2f7;color:#203454;margin:0;padding:36px}main{max-width:1320px;margin:auto}h1{font-size:30px}h2{font-size:22px}section{padding:26px;background:white;border:1px solid #cbd7e8;border-radius:10px;margin:22px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:9px 12px;border:1px solid #d9e2ef;text-align:left;word-break:break-word}th{background:#edf3fc}pre{white-space:pre-wrap;word-break:break-word;background:#18283c;color:#e5effb;padding:18px;border-radius:8px;font-size:14px;line-height:1.65}.pass{color:#167450}p{line-height:1.7}'
sections=[]
for i,item in enumerate(evidence):
    rows=''.join('<tr>'+''.join('<td>'+html.escape('NULL' if v is None else str(v))+'</td>' for v in row)+'</tr>' for row in item['rows'])
    sections.append(f'<section id="query-{i}"><h2>{html.escape(item["title"])}</h2><pre>{html.escape(item["query"])}</pre><table><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in item['columns'])+'</tr>'+rows+'</table></section>')
execution=(OUT/'sql-execution.txt').read_text(encoding='utf-8')
summary='\n'.join(line for line in execution.splitlines() if 'statements completed' in line or 'hashes unchanged' in line)
sections.insert(1,'<section id="execution"><h2>数据库脚本执行记录</h2><p>以下内容读取自执行日志，不是模拟终端。</p><pre>'+html.escape(summary)+'</pre><p class="pass">'+str(len(results))+' 项 MySQL 验证通过；演示数据为合成数据。</p></section>')
page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>实验五 MySQL 实际查询证据</title><style>'+css+'</style><main><h1>临客 LINK · 实验五数据库验收</h1><p>本页为实际 MySQL 查询结果的只读展示。数据来源：127.0.0.1:13316 / link_lab5。<br>采集时间：'+datetime.now(timezone.utc).isoformat()+'（UTC）。原始 SQL、查询结果 JSON 和执行日志随报告提供。</p>'+''.join(sections)+'</main></html>'
(OUT/'database-evidence.html').write_text(page,encoding='utf-8')
print(f'{len(results)} MySQL checks passed; evidence exported.')
