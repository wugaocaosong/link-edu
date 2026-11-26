from datetime import datetime

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from classroom_models import Classroom, ClassroomEvent
from extensions import db
from services.fraction_study import ROUNDS, STAGES, VERSION, study_evidence
from services.classroom_clock import timing
from study_models import StudyAttempt, StudyParticipant
from tenancy import Tenant, TenantMembership, tenant_id_for_request

bp = Blueprint('study', __name__, url_prefix='/api/study')


def participant():
    uid = int(get_jwt_identity())
    query = StudyParticipant.query.filter_by(user_id=uid)
    if request.headers.get('X-Tenant-ID'):
        return query.filter_by(tenant_id=tenant_id_for_request()).first()
    rows = (query.join(Tenant, StudyParticipant.tenant_id == Tenant.id)
            .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
            .filter(TenantMembership.user_id == uid, TenantMembership.status == 'active', Tenant.status == 'active')
            .limit(2).all())
    if len(rows) > 1:
        abort(409, description='此账号有多个实验机构，请指定实验机构')
    return rows[0] if rows else None


def attempts(p):
    return StudyAttempt.query.filter_by(participant_id=p.id).order_by(StudyAttempt.id).all()


def next_stage(rows):
    latest = {row.stage: row for row in rows}
    return next((s for s in STAGES if s not in latest or not latest[s].finished), None)


def study_session(sid):
    return StudyAttempt.query.filter_by(session_id=sid).first()


def owned_attempt(aid):
    p = participant()
    if not p:
        abort(404)
    return StudyAttempt.query.filter_by(id=aid, participant_id=p.id).first_or_404()


def active_attempt(aid):
    row = owned_attempt(aid)
    rows = attempts(db.session.get(StudyParticipant, row.participant_id))
    if row.stage != next_stage(rows) or any(r.stage == row.stage and r.number > row.number for r in rows):
        abort(409, description='请使用当前场次')
    return row


def field(data, key, limit):
    value = data.get(key)
    if not isinstance(value, str) or not 0 < len(value.strip()) <= limit:
        abort(400, description='文字字段缺失或超过长度')
    return value.strip()


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400)
    return data


def describe(row):
    room = db.session.get(Classroom, row.session_id) if row.session_id else None
    return {'id': row.id, 'stage': row.stage, 'number': row.number, 'clip': row.clip,
            'previous_id': row.previous_id, 'anomaly': row.anomaly, 'version': row.version,
            'created': row.created.isoformat() + 'Z', 'finished': bool(row.finished),
            'finished_at': row.finished.isoformat() + 'Z' if row.finished else None,
            'session_id': row.session_id, 'class_state': room.state if room else None,
            'active_seconds': timing(room)['active_elapsed'] if room and room.ended_at else None,
            'assessment': row.assessment, 'reflection': row.reflection, 'report': row.issued,
            'goal': row.goal}


@bp.get('')
@jwt_required()
def overview():
    p = participant()
    if not p:
        return jsonify(enrolled=False)
    rows = attempts(p)
    stage = next_stage(rows)
    return jsonify(enrolled=True, code=p.code, stage=stage,
                   arm=p.arm if stage != 'pre' else None, attempts=[describe(r) for r in rows])


@bp.post('/attempts')
@jwt_required()
def open_attempt():
    p = participant()
    if not p:
        abort(404)
    data = body()
    stage = data.get('stage')
    if stage not in STAGES or data.get('consent') is not True:
        abort(400, description='请确认本场录音录像授权')
    rows = attempts(p)
    if stage != next_stage(rows):
        abort(409, description='请按实验顺序进入本场')
    existing = [r for r in rows if r.stage == stage]
    if existing:
        return jsonify(describe(existing[-1]))
    row = StudyAttempt(participant_id=p.id, stage=stage, version=VERSION)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        row = StudyAttempt.query.filter_by(participant_id=p.id, stage=stage, number=1).one()
    return jsonify(describe(row))


@bp.post('/attempts/<int:aid>/assessment')
@jwt_required()
def assessment(aid):
    row = owned_attempt(aid)
    if row.stage not in ('pre', 'post'):
        abort(409)
    data = body()
    marks, duration = data.get('marks'), data.get('duration_ms')
    observed = [x for x in marks if x is not None] if isinstance(marks, list) else []
    if (type(duration) is not int or not 0 < duration <= 360000 or not isinstance(marks, list)
            or len(marks) > 2 or any(type(x) is not int or not 0 <= x <= duration for x in observed)
            or observed != sorted(set(observed)) or data.get('av_checked') is not True):
        abort(400, description='请核对录像、时间及两次机会标记')
    note = data.get('note', '')
    if not isinstance(note, str) or len(note) > 1000 or ((len(observed) < 2 or abs(duration-300000) > 2000) and not note.strip()):
        abort(400, description='请登记缺失机会或时长异常的原因')
    result = dict(marks=marks, duration_ms=duration, note=note, av_checked=True,
                  actor=field(data, 'actor', 40))
    if row.finished and row.assessment == result:
        return jsonify(describe(row))
    active_attempt(aid)
    row.assessment, row.finished = result, datetime.utcnow()
    db.session.commit()
    return jsonify(describe(row))


def events_for(row):
    return [e.to_dict() for e in ClassroomEvent.query.filter_by(session_id=row.session_id)
            .order_by(ClassroomEvent.id)]


@bp.post('/attempts/<int:aid>/reflection')
@jwt_required()
def reflect(aid):
    row = active_attempt(aid)
    room = db.session.get(Classroom, row.session_id) if row.session_id else None
    if row.stage not in ROUNDS or not room or room.state != 'ended':
        abort(409)
    data = body()
    at = data.get('at_ms')
    if type(at) is not int or not 0 <= at <= (room.ended_at-room.started_at).total_seconds()*1000:
        abort(400, description='片段时间超出课堂范围')
    reflection = dict(text=field(data, 'text', 2000), at_ms=at)
    if timing(room)['active_elapsed'] < 598:
        reflection['duration_note'] = field(data, 'duration_note', 1000)
    if row.reflection and row.reflection != reflection:
        abort(409, description='已保存独立自评')
    if not row.reflection:
        p = db.session.get(StudyParticipant, row.participant_id)
        packet, _ = study_evidence(events_for(row), p.arm)
        StudyAttempt.query.filter(StudyAttempt.id == aid, StudyAttempt.reflection.is_(None)).update(
            {StudyAttempt.reflection: reflection, StudyAttempt.packet: packet}, synchronize_session=False)
        db.session.commit()
        db.session.refresh(row)
        if row.reflection != reflection:
            abort(409)
    return jsonify(describe(row))


@bp.post('/attempts/<int:aid>/complete')
@jwt_required()
def complete(aid):
    row = owned_attempt(aid)
    data = body()
    if row.stage not in ROUNDS or not row.issued or data.get('reviewed_video') is not True:
        abort(409, description='请先阅读本组报告并回看录像')
    goal = field(data, 'goal', 2000) if row.stage == 'round1' else ''
    if row.finished and row.goal == goal:
        return jsonify(describe(row))
    active_attempt(aid)
    row.goal, row.finished = goal, datetime.utcnow()
    db.session.commit()
    return jsonify(describe(row))


@bp.get('/attempts/<int:aid>/evidence')
@jwt_required()
def evidence(aid):
    row = owned_attempt(aid)
    if row.stage not in ROUNDS or not row.reflection or not row.session_id:
        abort(409)
    events = events_for(row)
    p = db.session.get(StudyParticipant, row.participant_id)
    _, anchors = study_evidence(events, p.arm)
    # Playback and motion are research-only in the transcript arm. The browser
    # receives replay anchors for its own recording after independent reflection.
    return jsonify(turns=anchors, transcript=row.packet['transcript'])


@bp.errorhandler(400)
@bp.errorhandler(409)
def study_error(error):
    return jsonify(message=error.description), error.code
