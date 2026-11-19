import pytest
from datetime import datetime
from flask_jwt_extended import create_access_token
from sqlalchemy import event, inspect
from app import create_app
from extensions import db
from models import User, TrainingSession, Resource
from classroom_models import Classroom, ClassroomEvent
from adaptive_models import Answer, Quiz, Mastery, SkillMaterial, LearningProgress, Question
from services.adaptive import level_for, mastery
from services.adaptive_catalog import seed_catalog


@pytest.fixture
def lab(tmp_path):
    class Config:
        TESTING = True
        ADAPTIVE_ENABLED = True
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{tmp_path / "lab.db"}'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        JWT_SECRET_KEY = 'lab-test-secret-longer-than-thirty-two-characters'
    app = create_app(Config)
    with app.app_context():
        db.create_all()
        seed_catalog()
        db.session.commit()
        yield app.test_client()
        db.session.remove()


def headers(uid=95001):
    return {'Authorization': 'Bearer ' + create_access_token(identity=str(uid))}


def create(lab, key='test', skill=None):
    response = lab.post('/api/adaptive/quizzes', headers=headers(), json=dict(request_key=key, skill_id=skill))
    assert response.status_code == 200, response.json
    return response.json


def answers_for(quiz, correct=True):
    return {str(a.question_id): a.snapshot['answer'] if correct else next(k for k in a.snapshot['options'] if k != a.snapshot['answer']) for a in Answer.query.filter_by(quiz_id=quiz['id']).all()}


def test_cold_start_catalog_and_no_answer_leak(lab):
    data = lab.get('/api/adaptive/overview', headers=headers()).json
    assert len(data['skills']) == 6 and all(s['score'] is None for s in data['skills'])
    assert Question.query.count() == 36 and SkillMaterial.query.count() == 18
    quiz = create(lab)
    assert len(quiz['questions']) == 12
    assert all('answer' not in q and 'explanation' not in q for q in quiz['questions'])
    assert create(lab)['id'] == quiz['id']
    assert lab.post('/api/adaptive/quizzes', headers=headers(), json=dict(request_key='test',skill_id='pace')).status_code == 409


def test_submission_idempotence_invalid_rollback_and_permissions(lab):
    quiz = create(lab)
    url = f"/api/adaptive/quizzes/{quiz['id']}"
    assert lab.get(url, headers=headers(95002)).status_code == 404
    assert lab.get(url).status_code == 401
    answers = answers_for(quiz)
    bad = dict(answers); bad[next(iter(bad))] = 'Z'
    assert lab.post(url+'/submit',headers=headers(),json={'answers':bad}).status_code == 400
    assert db.session.get(Quiz,quiz['id']).status == 'open'
    assert all(a.selected is None for a in Answer.query.all())
    assert lab.post(url+'/submit',headers=headers(95002),json={'answers':answers}).status_code == 404
    result = lab.post(url+'/submit',headers=headers(),json={'answers':answers})
    assert result.status_code == 200 and all(v == 100 for v in result.json['scores'].values())
    assert lab.post(url+'/submit',headers=headers(),json={'answers':answers}).json == result.json
    assert lab.post(url+'/submit',headers=headers(),json={'answers':answers_for(quiz,False)}).status_code == 409
    assert Quiz.query.count() == 1
    assert all(s['quiz_score'] == 100 for s in lab.get('/api/adaptive/overview',headers=headers()).json['skills'])


def test_latest_three_and_thresholds(lab):
    for i in range(4):
        quiz=create(lab,str(i),'pace')
        lab.post(f"/api/adaptive/quizzes/{quiz['id']}/submit",headers=headers(),json={'answers':answers_for(quiz,i>0)})
    assert db.session.get(Mastery,(95001,'pace')).score == 100
    assert [level_for(v) for v in (None,0,59.99,60,79.99,80,100)] == [1,1,1,2,2,3,3]


def room(score=40):
    session=TrainingSession(user_id=95001,course_id=96001,status='completed')
    db.session.add(session); db.session.flush()
    r=Classroom(session_id=session.id,user_id=95001,state='ended',ended_at=datetime.utcnow(),report_state='completed',report_version=1)
    db.session.add(r); db.session.flush()
    e=ClassroomEvent(session_id=r.session_id,event_key='fixture',kind='transcript',at_ms=2000,payload={'text':'合成测试课堂证据'})
    db.session.add(e); db.session.flush()
    r.report={'dimensions':[{'key':'pace','score':score,'event_ids':[e.id]}]}
    db.session.commit()
    return r,e


def test_training_revision_mixed_and_exclusions(lab):
    r,e=room()
    assert next(s for s in mastery(95001) if s['skill_id']=='pace')['score']==40
    quiz=create(lab,skill='pace')
    lab.post(f"/api/adaptive/quizzes/{quiz['id']}/submit",headers=headers(),json={'answers':answers_for(quiz)})
    assert db.session.get(Mastery,(95001,'pace')).score==70
    r.report_version=2; r.report={'dimensions':[{'key':'pace','score':80,'event_ids':[e.id]}]}; db.session.commit()
    assert next(s for s in mastery(95001) if s['skill_id']=='pace')['score']==90
    for extra in ({'demo':True},{'synthetic':True},{'insufficient_evidence':True},{'generation_status':'failed'}):
        r.report={**extra,'dimensions':[{'key':'pace','score':80,'event_ids':[e.id]}]}; db.session.commit()
        assert next(s for s in mastery(95001) if s['skill_id']=='pace')['training_score'] is None
    r.report={'dimensions':[{'key':'pace','score':80,'event_ids':[999999]}]}; db.session.commit()
    assert next(s for s in mastery(95001) if s['skill_id']=='pace')['training_score'] is None


def test_paths_progress_resource_deactivation_and_ownership(lab):
    path=lab.post('/api/adaptive/paths',headers=headers(),json={}).json
    assert lab.post('/api/adaptive/paths',headers=headers(),json={}).json['id']==path['id']
    assert lab.get(f"/api/adaptive/paths/{path['id']}",headers=headers(95002)).status_code==404
    step=next(s for s in path['steps'] if s['kind']=='resource')
    url=f"/api/adaptive/steps/{step['id']}/complete"
    assert lab.post(url,headers=headers(95002),json={}).status_code==404
    assert lab.post(url,headers=headers(),json={}).status_code==200
    assert lab.post(url,headers=headers(),json={}).status_code==200
    assert LearningProgress.query.count()==1
    assert all(s['score'] is None for s in mastery(95001))
    material=SkillMaterial.query.filter_by(skill_id=step['skill_id'],level=1).first()
    db.session.get(Resource,material.resource_id).is_active=False; db.session.commit()
    assert lab.post(url,headers=headers(),json={}).status_code==409
    newpath=lab.post('/api/adaptive/paths',headers=headers(),json={}).json
    assert newpath['id']!=path['id']
    assert not any(s['kind']=='resource' and s['skill_id']==step['skill_id'] for s in newpath['steps'])


def test_disabled_never_queries_adaptive_tables():
    class Config:
        TESTING=True
        ADAPTIVE_ENABLED=False
        SQLALCHEMY_DATABASE_URI='sqlite://'
        SQLALCHEMY_TRACK_MODIFICATIONS=False
        JWT_SECRET_KEY='disabled-test-secret-longer-than-thirty-two'
    app=create_app(Config)
    statements=[]
    with app.app_context():
        event.listen(db.engine,'before_cursor_execute',lambda conn,cursor,statement,params,context,many: statements.append(statement))
        assert app.test_client().get('/api/adaptive/overview').status_code==404
        assert app.test_client().get('/api/health').status_code==200
        assert statements==[]
