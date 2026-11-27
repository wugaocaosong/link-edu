from contextvars import ContextVar
from functools import wraps


assistant_turn = ContextVar('assistant_turn', default=None)


def track_assistant_turn(function):
    @wraps(function)
    def tracked(owner, turn, *args, **kwargs):
        token = assistant_turn.set(turn)
        try:
            return function(owner, turn, *args, **kwargs)
        finally:
            assistant_turn.reset(token)
    return tracked
