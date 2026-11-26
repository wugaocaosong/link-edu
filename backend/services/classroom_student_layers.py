"""Three simulated students: hidden ideas, triggered disclosure, and round variants.

These are rehearsal roles. A state change is not a measurement of a real child.
"""
import base64
import re

PLAYBACK_RATE = 1.2
THINKING_MS = 260
REASON_PAUSE_MS = 480
GATED_STEPS = {'conclusion', 'reason', 'basis', 'challenge', 'shallow', 'confusion', 'stable', 'transfer', 'connect'}
REVEALING = {'open_probe', 'wait', 'scaffold'}
JUDGING = {'verdict', 'tell'}

ROLES = {
    'yu': {
        'code': 'A',
        'style': '主动质疑型',
        'hidden': '分成两份就有一半，还没比较两份是不是一样大。',
    },
    'lin': {
        'code': 'B',
        'style': '结论先行型',
        'hidden': '先说这一份是一半，理由只是数到了两份。',
    },
    'ming': {
        'code': 'C',
        'style': '建构求证型',
        'hidden': '两份一样大时，其中一份才是二分之一。',
    },
}

VARIANTS = {
    'round1': {'material': '折纸', 'conclusion': 'lin', 'reason': 'yu', 'verifier': 'ming', 'opener': 'lin'},
    'round2': {'material': '纸带', 'conclusion': 'lin', 'reason': 'yu', 'verifier': 'ming', 'opener': 'yu'},
    'live': {'material': '分数的初步认识', 'conclusion': 'lin', 'reason': 'yu', 'verifier': 'ming', 'opener': 'lin'},
}

CANON = {
    ('lin', 'conclusion'): '我觉得这一份是一半。',
    ('lin', 'basis'): '我是数出来的，有两份。',
    ('lin', 'shallow'): '哦。',
    ('lin', 'confusion'): '可我刚才就是这么想的。',
    ('yu', 'challenge'): '这两份不一样大，不也是一半吗？',
    ('yu', 'reason'): '我数了两份，所以我觉得这一块就是一半。',
    ('yu', 'confusion'): '那不一样大的时候，还能叫一半吗？',
    ('yu', 'shallow'): '哦，那我再看看。',
    ('ming', 'stable'): '要两份一样大，这一份才是一半。',
    ('ming', 'shallow'): '我先听听。',
    ('ming', 'connect'): '先说一半，和数了两份，是一回事吗？',
}


def classify_move(text):
    """Tell a casual question apart from a move that earns more of the hidden idea."""
    value = str(text or '')
    if re.search(r'为什么|怎么想|依据|理由|你怎么知道|再说说|怎么看出来|你是怎样', value):
        return 'open_probe'
    if re.search(r'慢慢说|我等你|等一等|你再想想|继续说|接着说', value):
        return 'wait'
    if re.search(r'比一比|比较|重合|对折|重叠|验证|你看这两', value):
        return 'scaffold'
    if re.search(r'不对|错了|不正确|不是这样|答错|正确|对了|真棒|很好', value):
        return 'verdict'
    if re.search(r'平均分|每份都一样|每份同样|一样大才', value) and not re.search(r'[?？]|谁', value):
        return 'tell'
    if re.search(r'[?？]|谁知道|说说|是不是|表示什么|你说|请说', value):
        return 'casual'
    return 'lecture'


def _variant(stage):
    return VARIANTS.get(stage, VARIANTS['live'])


def _transfer_line(stage):
    if stage == 'round2':
        return '如果换成一张纸，也得先看两份是不是一样大吗？'
    return '如果换成一条纸带，也得先看两份是不是一样长吗？'


def choose_cue(stage, sid, teacher_text, heard, prior_moves=()):
    """One step deeper only after an open probe, a wait, or a comparison."""
    script = _variant(stage)
    move = classify_move(teacher_text)
    heard = list(heard or [])
    revealing = move in REVEALING
    judging = move in JUDGING
    scaffolded = move == 'scaffold' or 'scaffold' in prior_moves
    if sid == script['verifier']:
        if judging:
            step = 'shallow'
        elif 'transfer' in heard and revealing:
            step = 'connect'
        elif revealing and scaffolded:
            step = 'transfer'
        else:
            step = 'stable'
    elif sid == script['reason']:
        if stage == 'round2' and not heard and not judging:
            step = 'reason'
        elif not heard and revealing:
            step = 'reason'
        elif not heard and judging:
            step = 'shallow'
        elif not heard:
            step = 'challenge'
        elif judging:
            step = 'confusion'
        elif revealing and 'reason' not in heard:
            step = 'reason'
        elif revealing:
            step = 'revise'
        else:
            step = 'challenge'
    else:
        if not heard:
            step = 'conclusion'
        elif judging:
            step = 'shallow'
        elif revealing:
            step = 'basis'
        else:
            step = 'conclusion'
    role = 'verifier' if sid == script['verifier'] else 'reason' if sid == script['reason'] else 'conclusion'
    return {
        'student_id': sid,
        'role': role,
        'step': step,
        'move': move,
        'material': script['material'],
        'instruction': _instruction(sid, step, script['material']),
    }


def _instruction(sid, step, material):
    style = ROLES[sid]['style']
    hidden = ROLES[sid]['hidden']
    if step in ('reason', 'basis', 'revise'):
        return f'{style}。这一步只说出隐藏依据的一句：{hidden}不补充正确讲法，不一次说完。'
    if step == 'transfer':
        return f'{style}。老师已经引导比较。用{material}之外的材料问一句是否同样要看两份一样大，不替别人回答。'
    if step == 'connect':
        return f'{style}。把另外两人已经说过的结论和理由连成一个问题，不给出标准答案。'
    if step == 'challenge':
        return f'{style}。只提出不等分是不是也算一半，不说数了两份，不说平均分。'
    if step == 'conclusion':
        return f'{style}。只说其中一份是一半，不解释。'
    return f'{style}。停在短反应或新的困惑，不展开隐藏依据：{hidden}'


def _leaks(text):
    return re.search(r'因为|所以|数了|平均|对折|重合', text or '')


def constrain_disclosure(sid, step, text, stage='live'):
    """Replace an over-explanation with the line this step is allowed to say."""
    from services.fraction_study import constrain_line
    value = str(text or '').strip()
    if step in ('conclusion', 'reason', 'basis'):
        return constrain_line(step, value)
    if step == 'revise':
        return value
    if step == 'transfer':
        if re.search(r'[?？]', value) and re.search(r'一样', value) and not re.search(r'数了|平均分就是', value):
            return value
        return _transfer_line(stage)
    allowed = {
        'challenge': lambda item: '一半' in item and not _leaks(item),
        'confusion': lambda item: re.search(r'[?？]|吗', item) and not re.search(r'数了|平均|对折', item),
        'shallow': lambda item: len(item) <= 16 and not _leaks(item),
        'stable': lambda item: re.search(r'一样|同样|相等', item) and not re.search(r'数了|对折', item),
        'connect': lambda item: re.search(r'[?？]', item) and len(item) <= 40 and not re.search(r'平均分就是', item),
    }
    rule = allowed.get(step)
    if rule and rule(value):
        return value
    return CANON.get((sid, step), value)


def preferred_raiser(teacher_text, prior_moves=()):
    """Active doubt comes from 小雨; connecting the class comes from 小明 after a comparison."""
    move = classify_move(teacher_text)
    if move == 'scaffold' or 'scaffold' in prior_moves:
        return 'ming'
    return 'yu'


def utterance_plan(step, text):
    """A short thinking pause, and a second pause before a reason clause."""
    value = str(text or '').strip()
    if step not in ('reason', 'basis', 'revise') or not value:
        return [{'kind': 'claim', 'text': value, 'pause_before_ms': THINKING_MS if value else 0}]
    parts = re.split(r'(?<=[，,])', value, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return [
            {'kind': 'claim', 'text': parts[0], 'pause_before_ms': THINKING_MS},
            {'kind': 'reason', 'text': parts[1], 'pause_before_ms': REASON_PAUSE_MS},
        ]
    return [
        {'kind': 'pause', 'text': '', 'pause_before_ms': REASON_PAUSE_MS},
        {'kind': 'reason', 'text': value, 'pause_before_ms': 0},
    ]


def silence_audio(ms, rate=24000):
    count = max(0, int(rate * int(ms) / 1000))
    return base64.b64encode(b'\x00\x00' * count).decode()


def reason_status(clock, onset_monotonic, now, playback_rate=PLAYBACK_RATE):
    """Whether the reason span had started when the teacher spoke."""
    if not clock or clock.get('reason_start_ms') is None:
        return 'no_reason'
    if not onset_monotonic:
        return 'not_started'
    played = max(0.0, (now - onset_monotonic) * 1000 * playback_rate)
    start = clock['reason_start_ms']
    total = clock.get('audio_ms') or 0
    if played + 40 < start:
        return 'not_started'
    if total and played + 40 >= total:
        return 'heard'
    return 'cut_off'
