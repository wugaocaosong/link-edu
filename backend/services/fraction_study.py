"""Training-only scripts and reproducible, group-specific review inputs."""
import hashlib
import json
import random
import re

from services.classroom_motion import motion_evidence
from services.classroom_student_layers import VARIANTS, choose_cue, classify_move

VERSION = 'unit-fraction-1'
STAGES = ('pre', 'round1', 'round2', 'post')
ROUNDS = {key: dict(VARIANTS[key]) for key in ('round1', 'round2')}


def allocate(roster, rng=None):
    """Balance odd strata in opposite directions; balance forms within each arm."""
    rng = rng or random.SystemRandom()
    if len(roster) != 16 or len({row['user_id'] for row in roster}) != 16:
        raise ValueError('需要16个不同的参试账号')
    rows = [dict(row, code=f'P{i:02}') for i, row in enumerate(roster, 1)]
    extra = rng.randrange(2)
    for experience in (False, True):
        layer = [row for row in rows if row['experience'] == experience]
        rng.shuffle(layer)
        split = len(layer) // 2 + (len(layer) % 2) * extra
        for i, row in enumerate(layer):
            row['arm'] = 'transcript' if i < split else 'multimodal'
        if len(layer) % 2:
            extra = 1 - extra
    for arm in ('transcript', 'multimodal'):
        group = [row for row in rows if row['arm'] == arm]
        rng.shuffle(group)
        for i, row in enumerate(group):
            row['first_form'] = 'A' if i < 4 else 'B'
    return rows


def playback_index(events):
    replies = {}
    for e in sorted(events, key=lambda item: (item['at_ms'], item['id'])):
        d = e['data']
        rid = d.get('reply_id')
        if not rid:
            continue
        if e['type'] == 'student':
            replies.setdefault(rid, {'event': e, 'start': None, 'end': None, 'problem': None})
        elif rid in replies:
            r = replies[rid]
            if e['type'] == 'playback_onset':
                r['start'] = r['start'] or e
            elif e['type'] == 'interrupt' or (e['type'] == 'playback' and d.get('status') in
                    ('playback_failed', 'playback_cancelled', 'cancelled')):
                r['problem'] = e
            elif e['type'] == 'playback' and d.get('status') == 'playback_completed':
                r['end'] = r['end'] or e
    return replies


def confirmed(r):
    return bool(r['end'] and not r['problem'])


def played_steps(history, sid):
    steps = []
    for reply in playback_index(history).values():
        data = reply['event']['data']
        if confirmed(reply) and data.get('student_id') == sid:
            steps.append(data.get('study_step') or data.get('disclosure_step'))
    return [step for step in steps if step]


def prior_moves(history):
    return [classify_move(event.get('data', {}).get('text', ''))
            for event in history if event.get('type') == 'transcript']


def student_cue(stage, sid, teacher_text, history):
    """Advance a role only after its previous utterance was actually played."""
    heard = played_steps(history, sid)
    cue = choose_cue(stage, sid, teacher_text, heard, prior_moves(history))
    if 'revise' in heard or ('compare' in heard and re.search('判断|现在|还是|所以|一半吗', teacher_text)):
        cue['step'] = 'revise'
        cue['instruction'] = '根据刚才的比较重新判断，并说明两份是否等大。'
    elif cue['move'] == 'scaffold' and cue['role'] != 'verifier' and heard:
        cue['step'] = 'compare'
        cue['instruction'] = '按老师当前材料比较两份，说明观察到的大小关系；不虚构看过材料。'
    return cue


def study_speaker(stage, text, history):
    heard = [reply['event']['data']['student_id'] for reply in playback_index(history).values() if confirmed(reply)]
    if heard and re.search('为什么|依据|理由|比一比|比较|对折|一样大|再想|现在|怎么知道', text):
        return heard[-1]
    script = ROUNDS[stage]
    order = []
    for sid in (script['opener'], script['conclusion'], script['reason'], script['verifier']):
        if sid not in order:
            order.append(sid)
    return next((sid for sid in order if sid not in heard), order[0])


def constrain_line(step, text):
    """Keep the first disclosure stable, even when the language model over-explains."""
    if step not in ('conclusion', 'reason', 'basis'):
        return text
    mentions_equal = re.search(r'一样|相等|等大|同样|平均|对折|重合|大小', text)
    gives_reason = re.search(r'因为|所以|分成|数了|两[份块]|2[份块]', text)
    half = re.search(r'一半|二分之一|1/2', text)
    if step == 'conclusion':
        return text if half and not (mentions_equal or gives_reason) else '我觉得这一份是一半。'
    if step == 'reason':
        return text if half and gives_reason and not mentions_equal else '我数了两份，所以我觉得这一块就是一半。'
    return text if gives_reason and not mentions_equal else '我是数出来的，有两份。'


def study_evidence(events, arm):
    if arm not in ('transcript', 'multimodal'):
        raise ValueError('未知实验条件')
    replies = playback_index(events)
    lines = [(e['at_ms'], e['id'], '教师', e['data']['text']) for e in events
             if e['type'] == 'transcript' and e['data'].get('source') == 'asr_final' and e['data'].get('text')]
    playback = []
    for rid, r in replies.items():
        event, start, end, problem = (r[k] for k in ('event', 'start', 'end', 'problem'))
        data = event['data']
        if confirmed(r):
            lines.append(((start or end)['at_ms'], event['id'], data.get('name') or data['student_id'], data['text']))
        row = {'reply_id': rid, 'event_id': event['id'],
               'start_ms': start['at_ms'] if start else None,
               'end_ms': (problem or end)['at_ms'] if problem or end else None,
               'status': 'completed' if confirmed(r) else 'interrupted_or_failed' if problem else 'unconfirmed'}
        reason = (problem or {}).get('data', {}).get('reason_status') if problem else None
        if reason in ('no_reason', 'not_started', 'cut_off', 'heard'):
            row['reason_status'] = reason
        playback.append(row)
    ordered = sorted(lines)
    transcript = [{'turn': i, 'speaker': speaker, 'text': text}
                  for i, (_, _, speaker, text) in enumerate(ordered, 1)]
    packet = {'transcript': transcript}
    if arm == 'multimodal':
        turns = {row[1]: i for i, row in enumerate(ordered, 1)}
        packet['playback'] = [dict(row, turn=turns.get(row['event_id'])) for row in playback]
        packet['teacher_motion'] = motion_evidence(events)
    return packet, [{'turn': i, 'event_id': eid, 'at_ms': ms}
                    for i, (ms, eid, _, _) in enumerate(ordered, 1)]


def capture_summary(evidence):
    """Coordinator-only counts from the full research export, independent of arm."""
    playback = evidence['playback']
    complete = [row for row in playback if row['status'] == 'completed']
    return {
        'replies': len(playback),
        'completed_replies': len(complete),
        'completed_without_onset': [r['reply_id'] for r in complete if r['start_ms'] is None],
        'completed_with_both_timestamps': sum(r['start_ms'] is not None and
                                              r['end_ms'] is not None for r in complete),
        'interrupted_or_failed': sum(r['status'] == 'interrupted_or_failed' for r in playback),
        'unconfirmed': sum(r['status'] == 'unconfirmed' for r in playback),
        'motion_samples': {
            key: {k: value[k] for k in ('observed_samples', 'total_samples')}
            for key, value in evidence['teacher_motion']['modalities'].items()
        },
    }


def digest(packet):
    return hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()
