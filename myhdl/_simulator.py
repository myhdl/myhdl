""" Simulator internals """

_siglist = []
_futureEvents = []
_time = 0

def now():
    return _time
