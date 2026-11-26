"""Optional local MM-TBA video analysis for a finished classroom recording."""

import json
import math
import subprocess
import threading
import uuid
from collections import Counter
from pathlib import Path

from extensions import db
from classroom_models import ClassroomEvent

LABELS = {'Normal', 'Writing', 'Pointing'}
_running = set()
_lock = threading.Lock()


def _event(sid, kind, at_ms, payload):
    db.session.add(ClassroomEvent(session_id=sid, event_key=uuid.uuid4().hex,
                                  kind=kind, at_ms=max(0, int(at_ms)), payload=payload))
    db.session.commit()


def _wall_time(video_ms, segments):
    for segment in segments:
        start = segment['videoStart']
        length = segment['wallEnd'] - segment['wallStart']
        if start <= video_ms <= start + length:
            return round(segment['wallStart'] + video_ms - start)
    return None


def validate_segments(raw):
    try:
        segments = json.loads(raw)
        if not isinstance(segments, list) or not 1 <= len(segments) <= 100:
            return None
        for item in segments:
            if not isinstance(item, dict) or any(type(item.get(key)) not in (int, float)
                or not math.isfinite(item[key]) or item[key] < 0
                for key in ('wallStart', 'wallEnd', 'videoStart')):
                return None
            if item['wallEnd'] <= item['wallStart']:
                return None
        return segments
    except (TypeError, ValueError):
        return None


def start_mm_tba(app, sid, video_path, output_dir, segments):
    with _lock:
        if sid in _running:
            return False
        _running.add(sid)
    with app.app_context():
        _event(sid, 'mm_tba_status', 0, {'status': 'running', 'message': 'MM-TBA 正在分析本机录像'})

    def run():
        with app.app_context():
            try:
                script = Path(app.root_path).parent / 'scripts' / 'Run-MM-TBAChunkedAnalysis.ps1'
                subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                    '-File', str(script), '-VideoPath', str(video_path), '-OutputDirectory', str(output_dir),
                    '-Device', 'cuda:0', '-SkipOverlay'], check=True, timeout=7200,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors='replace')
                events = json.loads((output_dir / 'action-events.json').read_text(encoding='utf-8-sig'))
                counts = Counter()
                for sample in events if isinstance(events, list) else []:
                    if not isinstance(sample, dict):
                        continue
                    try:
                        video_ms = float(sample['time_seconds']) * 1000
                    except (KeyError, TypeError, ValueError):
                        continue
                    if not math.isfinite(video_ms):
                        continue
                    at_ms = _wall_time(video_ms, segments)
                    if at_ms is None:
                        continue
                    for person in sample.get('people', [])[:3]:
                        for action in person.get('actions', [])[:3]:
                            label = action.get('label')
                            score = action.get('score')
                            if label not in LABELS or type(score) not in (int, float) or not math.isfinite(score):
                                continue
                            counts[label] += 1
                            _event(sid, 'mm_tba_action', at_ms, {
                                'label': label, 'confidence': round(float(score), 3),
                                'model': 'MM-TBA SlowFast ACRN', 'video_ms': round(video_ms),
                                'notice': '模型预测，需回看录像核对；Normal 是动作类别，不表示表情正常。',
                            })
                _event(sid, 'mm_tba_status', 0, {'status': 'completed', 'counts': dict(counts),
                    'message': 'MM-TBA 分析完成；请回看低置信度标签。'})
            except Exception:
                db.session.rollback()
                _event(sid, 'mm_tba_status', 0, {'status': 'failed',
                    'message': 'MM-TBA 分析失败，请检查本机 GPU/WSL 环境或录像格式后重试。'})
            finally:
                video_path.unlink(missing_ok=True)
                for chunk in (output_dir / 'chunks').glob('segment_*.mp4'):
                    chunk.unlink(missing_ok=True)
                db.session.remove()
                with _lock:
                    _running.discard(sid)
    threading.Thread(target=run, daemon=True).start()
    return True
