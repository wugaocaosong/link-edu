"""Coordinator-only commands. No allocation, script or report-import HTTP endpoint."""
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path

import click
from flask.cli import with_appcontext

from classroom_models import Classroom, ClassroomEvent
from extensions import db
from services.classroom_providers import ProviderError
from services.fraction_study import ROUNDS, VERSION, allocate, capture_summary, digest, playback_index, study_evidence
from services.study_review import compile_review, validate_issue
from study_models import StudyAttempt, StudyParticipant
from study_routes import attempts, describe, events_for, next_stage
from tenancy import TenantMembership


@click.group()
def study():
    """《认识几分之一》实验协调工具"""


def write_json(path, data):
    # Exclusive create prevents overwriting an earlier export.
    with path.open('x', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2)


def find_attempt(aid):
    row = db.session.get(StudyAttempt, aid)
    if not row:
        raise click.ClickException('场次不存在')
    return row


@study.command('allocate')
@click.argument('tenant', type=int)
@click.argument('roster', type=click.Path(exists=True, path_type=Path))
@with_appcontext
def allocate_command(tenant, roster):
    """Import a private CSV with columns user_id,experience (0/1)."""
    if StudyParticipant.query.filter_by(tenant_id=tenant).filter(StudyParticipant.code.like('P%')).first():
        raise click.ClickException('该机构已有分配记录')
    with roster.open(encoding='utf-8-sig', newline='') as source:
        rows = []
        for item in csv.DictReader(source):
            if item.get('experience') not in ('0', '1') or not (item.get('user_id') or '').isdigit():
                raise click.ClickException('请检查 user_id 和 experience')
            uid = int(item['user_id'])
            if StudyParticipant.query.filter_by(tenant_id=tenant, user_id=uid).first():
                raise click.ClickException('试跑账号不可列入正式样本')
            if not TenantMembership.query.filter_by(tenant_id=tenant, user_id=uid, status='active').first():
                raise click.ClickException(f'账号 {uid} 不是该机构的有效成员')
            rows.append(dict(user_id=uid, experience=item['experience'] == '1'))
    try:
        allocation = allocate(rows)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    db.session.add_all(StudyParticipant(tenant_id=tenant, **r) for r in allocation)
    db.session.commit()
    click.echo('16 人分配已保存。用 roster 导出协调员用表。')


@study.command('pilot')
@click.argument('tenant', type=int)
@click.argument('user_id', type=int)
@click.option('--arm', type=click.Choice(['transcript','multimodal']), default='multimodal')
@with_appcontext
def pilot(tenant, user_id, arm):
    """Register a non-participant for a device rehearsal outside the P01–P16 roster."""
    code = 'QA-M' if arm == 'multimodal' else 'QA-T'
    if not TenantMembership.query.filter_by(tenant_id=tenant,user_id=user_id,status='active').first():
        raise click.ClickException('试跑账号须为该机构有效成员')
    if StudyParticipant.query.filter_by(tenant_id=tenant).filter(
            (StudyParticipant.code == code) | (StudyParticipant.user_id == user_id)).first():
        raise click.ClickException('该试跑位或账号已有登记')
    db.session.add(StudyParticipant(tenant_id=tenant,user_id=user_id,experience=False,code=code,
                                   arm=arm,first_form='A' if arm=='multimodal' else 'B'))
    db.session.commit()
    click.echo(code)


@study.command('roster')
@click.argument('tenant', type=int)
@click.argument('output', type=click.Path(path_type=Path))
@with_appcontext
def roster_command(tenant, output):
    data = []
    for p in StudyParticipant.query.filter_by(tenant_id=tenant).filter(
            StudyParticipant.code.like('P%')).order_by(StudyParticipant.code):
        rows = attempts(p)
        training = {r.stage: db.session.get(Classroom, r.session_id).started_at
                    for r in rows if r.session_id}
        interval = ((training['round2'] - training['round1']).total_seconds() / 86400
                    if len(training) == 2 else None)
        data.append(dict(code=p.code, user_id=p.user_id, experience=p.experience, arm=p.arm,
                         pre=p.first_form, post='B' if p.first_form == 'A' else 'A',
                         interval_days=interval, stage=next_stage(rows), attempts=[describe(r) for r in rows]))
    write_json(output, data)


@study.command('packet')
@click.argument('aid', type=int)
@click.argument('output', type=click.Path(path_type=Path))
@with_appcontext
def packet_command(aid, output):
    row = find_attempt(aid)
    if row.packet is None:
        raise click.ClickException('请先提交独立自评')
    write_json(output, dict(attempt=aid, sha256=digest(row.packet), input=row.packet, version=row.version))


@study.command('generate')
@click.argument('aid', type=int)
@click.argument('output', type=click.Path(path_type=Path))
@with_appcontext
def generate_command(aid, output):
    """Write a review file from the sealed packet. Does not issue it."""
    row = find_attempt(aid)
    if row.packet is None:
        raise click.ClickException('请先提交独立自评')
    try:
        document = compile_review(aid, row.packet)
    except (ValueError, ProviderError) as exc:
        raise click.ClickException(str(exc)) from exc
    write_json(output, document)


@study.command('speech-probe')
@with_appcontext
def speech_probe():
    """Open and finish a silent recognition probe. Unconfirmed text is not stored."""
    from services.classroom_speech import probe_asr
    try:
        probe_asr()
    except Exception as exc:
        detail = str(exc) if isinstance(exc, (ProviderError, ValueError)) else '语音识别探针失败'
        raise click.ClickException(
            f'{detail}。请检查讯飞密钥、权限和到 wss://iat.xf-yun.com/v1 的网络。未确认文本不会入档。') from exc
    click.echo('语音识别探针已完成')


@study.command('issue')
@click.argument('aid', type=int)
@click.argument('report', type=click.Path(exists=True, path_type=Path))
@with_appcontext
def issue_command(aid, report):
    row = find_attempt(aid)
    data = json.loads(report.read_text(encoding='utf-8-sig'))
    if (row.packet is None or not isinstance(data, dict) or data.get('attempt') != aid
            or data.get('sha256') != digest(row.packet)
            or any(not isinstance(data.get(k), str) or not data[k].strip()
                   for k in ('text', 'model', 'rubric_version', 'template_version'))):
        raise click.ClickException('报告场次、输入摘要或版本信息无效')
    try:
        validate_issue(row.packet, data)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    fields = ('sha256', 'text', 'model', 'rubric_version', 'template_version')
    if row.issued and all(row.issued[k] == data[k] for k in fields):
        return
    participant = db.session.get(StudyParticipant, row.participant_id)
    cohort = 'QA%' if participant.code.startswith('QA') else 'P%'
    prior = (StudyAttempt.query.join(StudyParticipant)
             .filter(StudyParticipant.tenant_id == participant.tenant_id, StudyAttempt.version == row.version,
                     StudyParticipant.code.like(cohort), StudyAttempt.issued.is_not(None)).order_by(StudyAttempt.id).first())
    if prior and any(prior.issued[k] != data[k] for k in ('model','rubric_version','template_version')):
        raise click.ClickException('与本实验首份已发放报告的模型、量规或模板版本不一致')
    updated = StudyAttempt.query.filter(StudyAttempt.id == aid, StudyAttempt.issued.is_(None)).update(
        {StudyAttempt.issued: {**{k: data[k] for k in fields}, 'issued_at': datetime.utcnow().isoformat()+'Z'}},
        synchronize_session=False)
    if updated != 1:
        raise click.ClickException('本场已发放报告，请保留原件')
    db.session.commit()


@study.command('research-export')
@click.argument('aid', type=int)
@click.argument('output', type=click.Path(path_type=Path))
@with_appcontext
def research_export(aid, output):
    row = find_attempt(aid)
    p = db.session.get(StudyParticipant, row.participant_id)
    result = dict(participant=p.code, arm=p.arm, **describe(row))
    if row.session_id:
        events = events_for(row)
        evidence, anchors = study_evidence(events, 'multimodal')
        result.update(evidence=evidence, capture_summary=capture_summary(evidence),
                      turns=anchors, issued_input=row.packet,
                      planned=ROUNDS[row.stage], attempted=[
                          {'reply_id': rid, 'event_id': r['event']['id'],
                           'student_id':r['event']['data']['student_id'],
                           'step': r['event']['data'].get('study_step'),
                           'fallback':r['event']['data'].get('script_fallback', False)}
                          for rid, r in playback_index(events).items()],
                      invitations=[e for e in events if e['type']=='study_invitation'],
                      observations=[e for e in events if e['type']=='study_observation'],
                      interruptions=[e for e in events if e['type'] in ('pause','resume','error','interrupt','study_generation_failed')])
    write_json(output, result)


@study.command('observe')
@click.argument('aid', type=int)
@click.argument('at_ms', type=click.IntRange(min=0))
@click.argument('category',type=click.Choice(['teacher_skipped','cue_missing','audio_unclear','other']))
@click.argument('note')
@with_appcontext
def observe(aid, at_ms, category, note):
    row = find_attempt(aid)
    room = db.session.get(Classroom, row.session_id) if row.session_id else None
    if not room or not note.strip() or at_ms > ((room.ended_at or datetime.utcnow())-room.started_at).total_seconds()*1000:
        raise click.ClickException('请提供有效课堂时间及观察依据')
    db.session.add(ClassroomEvent(session_id=row.session_id,at_ms=at_ms,event_key=uuid.uuid4().hex,
                                  kind='study_observation',payload={'category':category,'note':note.strip()}))
    db.session.commit()


@study.command('repeat')
@click.argument('aid', type=int)
@click.argument('reason')
@with_appcontext
def repeat(aid, reason):
    """Record why a fresh attempt is required; retain the earlier exposure."""
    row = find_attempt(aid)
    rows = attempts(db.session.get(StudyParticipant, row.participant_id))
    room = db.session.get(Classroom, row.session_id) if row.session_id else None
    if rows[-1].id != aid or not reason.strip() or (room and room.state != 'ended'):
        raise click.ClickException('只可补测最近场次。请先结束活动课堂并登记原因。')
    replacement = StudyAttempt(participant_id=row.participant_id, stage=row.stage, number=row.number+1,
                               previous_id=aid, anomaly=reason.strip(), version=VERSION)
    db.session.add(replacement)
    db.session.commit()
    click.echo(f'新场次 {replacement.id}，关联原场次 {aid}')
