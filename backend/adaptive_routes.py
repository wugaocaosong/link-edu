from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, Conflict
from extensions import db
from models import User
from adaptive_models import Quiz, LearningPath, PathStep
from services import adaptive as service

adaptive_bp = Blueprint('adaptive', __name__, url_prefix='/api/adaptive')


def transaction(fn):
    @wraps(fn)
    @jwt_required()
    def wrapped(*args, **kwargs):
        try:
            identity = str(get_jwt_identity())
            if not identity.isdigit():
                raise NotFound('用户不存在')
            uid = int(identity)
            # Serialize a user's adaptive writes across processes, including idempotent submissions.
            if not User.query.filter_by(id=uid).with_for_update().first():
                raise NotFound('用户不存在')
            result = fn(uid, *args, **kwargs)
            db.session.commit()
            return jsonify(result)
        except HTTPException as error:
            db.session.rollback()
            return jsonify(message=error.description), error.code
        except Exception:
            db.session.rollback()
            raise
    return wrapped


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest('请求必须为 JSON 对象')
    return data


@adaptive_bp.get('/overview')
@transaction
def overview(uid):
    skills = service.mastery(uid)
    history = Quiz.query.filter_by(user_id=uid).order_by(Quiz.id.desc()).limit(20).all()
    path = LearningPath.query.filter_by(user_id=uid).order_by(LearningPath.id.desc()).first()
    return dict(skills=skills, history=[dict(id=q.id, status=q.status, skill_id=q.skill_id, scores=q.scores, created_at=q.created_at.isoformat()) for q in history],
                path=service.path_payload(path), rule='测验与有效训练各占 50%；只有一类时使用该类。低于60基础学习，60–79专项巩固，80及以上提升练习。')


@adaptive_bp.post('/quizzes')
@transaction
def create(uid):
    return service.quiz_payload(service.create_quiz(uid, body()))


@adaptive_bp.get('/quizzes/<int:quiz_id>')
@transaction
def get_quiz(uid, quiz_id):
    return service.quiz_payload(service.owned_quiz(uid, quiz_id))


@adaptive_bp.post('/quizzes/<int:quiz_id>/submit')
@transaction
def submit(uid, quiz_id):
    return service.quiz_payload(service.submit_quiz(uid, quiz_id, body()))


@adaptive_bp.post('/paths')
@transaction
def generate(uid):
    return service.path_payload(service.generate_path(uid))


@adaptive_bp.get('/paths/<int:path_id>')
@transaction
def get_path(uid, path_id):
    path = LearningPath.query.filter_by(id=path_id, user_id=uid).first()
    if not path:
        raise NotFound('学习路径不存在')
    return service.path_payload(path)


@adaptive_bp.post('/steps/<int:step_id>/complete')
@transaction
def complete(uid, step_id):
    step = PathStep.query.join(LearningPath).filter(PathStep.id == step_id, LearningPath.user_id == uid).first()
    if not step:
        raise NotFound('学习步骤不存在')
    if step.kind == 'practice' and not step.practice_plan_id:
        service.complete_step(uid, step)
        return dict(id=step.id, status=step.status, basis='self_report')
    if step.kind != 'resource':
        raise Conflict('测验和训练须通过实际完成来记录进度')
    material = db.session.get(service.SkillMaterial, step.material_id)
    if not material or not service.materials_for(material.skill_id, material.level):
        raise Conflict('资源已停用，请更新学习路径')
    service.complete_step(uid, step)
    return dict(id=step.id, status=step.status)
