"""Deterministic learning rules; all writes run in the caller's transaction."""
import hashlib
import json
import math
import random
from datetime import datetime
from werkzeug.exceptions import BadRequest, Conflict, NotFound
from extensions import db
from models import Course, Resource
from classroom_models import Classroom, ClassroomEvent, PracticePlan
from adaptive_models import Skill, SkillMaterial, Question, Quiz, Answer, Mastery, LearningPath, PathStep, LearningProgress


def level_for(score):
    return 1 if score is None or score < 60 else 2 if score < 80 else 3


def mastery(user_id):
    quizzes = Quiz.query.filter_by(user_id=user_id, status='submitted').order_by(Quiz.submitted_at.desc(), Quiz.id.desc()).all()
    rooms = Classroom.query.filter_by(user_id=user_id, report_state='completed').order_by(Classroom.ended_at.desc(), Classroom.session_id.desc()).all()
    training = {}
    for room in rooms:
        report = room.report or {}
        if not isinstance(report, dict) or report.get('demo') or report.get('synthetic') or report.get('insufficient_evidence'):
            continue
        if report.get('generation_status') in ('failed', 'pending', 'processing'):
            continue
        valid_ids = {e.id for e in ClassroomEvent.query.filter_by(session_id=room.session_id).all() if e.kind in ('transcript', 'student', 'pose', 'vision')}
        dimensions = report.get('dimensions')
        for dim in dimensions if isinstance(dimensions, list) else []:
            if not isinstance(dim, dict):
                continue
            key, score = dim.get('key'), dim.get('score')
            if key in training or type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 100:
                continue
            if dim.get('insufficient_evidence') or dim.get('status') in ('insufficient', 'insufficient_evidence', 'unavailable'):
                continue
            ids = dim.get('event_ids')
            if not isinstance(ids, list) or not any(type(i) is int and i in valid_ids for i in ids):
                continue
            training[key] = {'score': score, 'session_id': room.session_id, 'version': room.report_version,
                             'event_ids': [i for i in ids if type(i) is int and i in valid_ids]}
    result = []
    for skill in Skill.query.order_by(Skill.ordinal).all():
        samples = [{'quiz_id': q.id, 'score': q.scores[skill.id]} for q in quizzes if skill.id in (q.scores or {})][:3]
        quiz_score = round(sum(s['score'] for s in samples) / len(samples), 2) if samples else None
        evidence = {'quizzes': samples, 'training': training.get(skill.id), 'rule_version': 'lab5-v1'}
        training_score = training.get(skill.id, {}).get('score')
        values = [v for v in (quiz_score, training_score) if v is not None]
        score = round(sum(values) / len(values), 2) if values else None
        row = db.session.get(Mastery, (user_id, skill.id))
        if row is None:
            row = Mastery(user_id=user_id, skill_id=skill.id)
            db.session.add(row)
        row.quiz_score, row.training_score, row.score, row.evidence = quiz_score, training_score, score, evidence
        row.updated_at = datetime.utcnow()
        result.append(dict(skill_id=skill.id, name=skill.name, description=skill.description, score=score,
                           quiz_score=quiz_score, training_score=training_score, evidence=evidence,
                           level=level_for(score), label='待诊断' if score is None else ['基础学习', '专项巩固', '提升练习'][level_for(score)-1]))
    db.session.flush()
    return result


def quiz_payload(quiz):
    items = []
    for row in Answer.query.filter_by(quiz_id=quiz.id).order_by(Answer.ordinal).all():
        item = {k: v for k, v in row.snapshot.items() if k not in ('answer', 'explanation')}
        item['id'] = row.question_id
        if quiz.status == 'submitted':
            item.update(answer=row.snapshot['answer'], explanation=row.snapshot['explanation'], selected=row.selected, correct=row.correct)
        items.append(item)
    return dict(id=quiz.id, status=quiz.status, skill_id=quiz.skill_id, scores=quiz.scores,
                created_at=quiz.created_at.isoformat(), questions=items)


def create_quiz(user_id, data):
    key = data.get('request_key')
    if not isinstance(key, str) or not 1 <= len(key) <= 64:
        raise BadRequest('请提供有效的请求编号')
    skill_id = data.get('skill_id') or None
    if skill_id is not None and (not isinstance(skill_id, str) or not db.session.get(Skill, skill_id)):
        raise BadRequest('技能不存在')
    old = Quiz.query.filter_by(user_id=user_id, request_key=key).first()
    if old:
        if old.skill_id != skill_id:
            raise Conflict('请求编号已用于另一份测验')
        return old
    quiz = Quiz(user_id=user_id, request_key=key, skill_id=skill_id)
    db.session.add(quiz)
    db.session.flush()
    rng = random.Random(f'{user_id}:{quiz.id}:{key}')
    selected = []
    for skill in Skill.query.order_by(Skill.ordinal).all():
        if skill_id and skill.id != skill_id:
            continue
        pool = Question.query.filter_by(skill_id=skill.id, active=True).order_by(Question.id).all()
        count = 6 if skill_id else 2
        if len(pool) < count:
            raise Conflict('题库尚未准备完整')
        selected.extend(rng.sample(pool, count))
    for ordinal, q in enumerate(selected):
        db.session.add(Answer(quiz_id=quiz.id, question_id=q.id, ordinal=ordinal,
            snapshot=dict(skill_id=q.skill_id, level=q.level, prompt=q.prompt, options=q.options,
                          answer=q.answer, explanation=q.explanation)))
    db.session.flush()
    return quiz


def owned_quiz(user_id, quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user_id).first()
    if not quiz:
        raise NotFound('测验不存在')
    return quiz


def submit_quiz(user_id, quiz_id, data):
    quiz = owned_quiz(user_id, quiz_id)
    answers = data.get('answers')
    rows = Answer.query.filter_by(quiz_id=quiz.id).order_by(Answer.ordinal).all()
    if not isinstance(answers, dict) or set(answers) != {str(a.question_id) for a in rows}:
        raise BadRequest('请完整回答所有题目')
    for row in rows:
        value = answers[str(row.question_id)]
        if not isinstance(value, str) or value not in row.snapshot['options']:
            raise BadRequest('答案选项无效')
    if quiz.status == 'submitted':
        if any(row.selected != answers[str(row.question_id)] for row in rows):
            raise Conflict('本次测验已经提交，不能更改答案')
        return quiz
    grouped = {}
    for row in rows:
        row.selected = answers[str(row.question_id)]
        row.correct = row.selected == row.snapshot['answer']
        grouped.setdefault(row.snapshot['skill_id'], []).append(row.correct)
    quiz.scores = {k: round(100 * sum(v) / len(v), 2) for k, v in grouped.items()}
    quiz.status, quiz.submitted_at = 'submitted', datetime.utcnow()
    db.session.flush()
    mastery(user_id)
    # Only diagnostic/retest steps are completed by a submitted quiz, never by a manual click.
    for step in PathStep.query.join(LearningPath).filter(LearningPath.user_id == user_id, PathStep.status == 'pending').all():
        path = db.session.get(LearningPath, step.path_id)
        if step.kind in ('diagnostic', 'retest') and step.skill_id in grouped and quiz.created_at >= path.created_at:
            complete_step(user_id, step)
    return quiz


def materials_for(skill_id, level):
    return SkillMaterial.query.join(Resource, Resource.id == SkillMaterial.resource_id).join(Course, Course.id == SkillMaterial.course_id).filter(
        SkillMaterial.skill_id == skill_id, SkillMaterial.level == level, Resource.is_active.is_(True), Course.is_active.is_(True)).first()


def generate_path(user_id):
    skills = mastery(user_id)
    available = {s['skill_id']: materials_for(s['skill_id'], s['level']) for s in skills}
    plans = {}
    for room in Classroom.query.filter_by(user_id=user_id, report_state='completed').order_by(Classroom.ended_at.desc()).all():
        valid = [s for s in skills if (s['evidence']['training'] or {}).get('session_id') == room.session_id]
        if not valid:
            continue
        from services.classroom_practice import ensure_plans
        for p in ensure_plans(room):
            if p.status == 'suggested' and p.dimension in {s['skill_id'] for s in valid}:
                plans.setdefault(p.dimension, p)
    db.session.flush()
    signature = dict(skills=skills, materials={k: v.id if v else None for k,v in available.items()},
                     plans={k:v.id for k,v in plans.items()})
    fingerprint = hashlib.sha256(json.dumps(signature, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    old = LearningPath.query.filter_by(user_id=user_id, fingerprint=fingerprint).first()
    if old:
        return old
    path = LearningPath(user_id=user_id, fingerprint=fingerprint)
    db.session.add(path)
    db.session.flush()
    ordinal = 0
    for skill in sorted(skills, key=lambda s: (-1 if s['score'] is None else s['score'], s['skill_id'])):
        material = available[skill['skill_id']]
        kinds = [('diagnostic', '完成技能诊断')] if skill['score'] is None else []
        if material:
            kinds.append(('resource', f"{skill['name']} · {skill['label'] if skill['score'] is not None else '基础学习'}"))
        kinds.extend([('practice', f"练习{skill['name']}"), ('retest', f"复测{skill['name']}")])
        for kind, title in kinds:
            ordinal += 1
            db.session.add(PathStep(path_id=path.id, skill_id=skill['skill_id'], ordinal=ordinal, kind=kind, title=title,
                reason=skill, material_id=material.id if material and kind == 'resource' else None,
                practice_plan_id=plans[skill['skill_id']].id if kind == 'practice' and skill['skill_id'] in plans else None))
    db.session.flush()
    return path


def complete_step(user_id, step):
    if step.status != 'completed':
        step.status = 'completed'
        db.session.add(LearningProgress(user_id=user_id, step_id=step.id))


def path_payload(path):
    if not path:
        return None
    steps = []
    for s in PathStep.query.filter_by(path_id=path.id).order_by(PathStep.ordinal).all():
        material = db.session.get(SkillMaterial, s.material_id) if s.material_id else None
        active = bool(material and materials_for(material.skill_id, material.level)) if s.kind == 'resource' else True
        practice = db.session.get(PracticePlan, s.practice_plan_id) if s.practice_plan_id else None
        if practice and practice.status == 'completed':
            complete_step(path.user_id, s)
        steps.append(dict(id=s.id, kind=s.kind, skill_id=s.skill_id, title=s.title, status=s.status, reason=s.reason,
                          available=active, content=material.content if material and active else None,
                          practice_plan_id=practice.id if practice else None, practice_status=practice.status if practice else None))
    return dict(id=path.id, created_at=path.created_at.isoformat(), steps=steps)
