from __future__ import absolute_import
import warnings

from myhdl._Signal import _Signal, _DelayedSignal
from myhdl._simulator import _siglist


class BusContentionWarning(UserWarning):
    pass

warnings.filterwarnings('always', r".*", BusContentionWarning)


def Tristate(val, delay=None):
    """ Return a new Tristate(default or delay 0) or DelayedTristate """
    if delay is not None:
        if delay < 0:
            raise TypeError("Signal: delay should be >= 0")
        return _DelayedTristate(val, delay)
    else:
        return _Tristate(val)


class _Tristate(_Signal):

    def __init__(self, val):
        self._drivers = []
        super(Tristate, self).__init__(val)
        self._val = None

    def driver(self):
        d = _TristateDriver(self)
        self._drivers.append(d)
        return d

    def _resolve(self):
        next = None
        for d in self._drivers:
            if next is None:
                next = d._next
            elif d._next is not None:
                warnings.warn("Bus contention", category=BusContentionWarning)
                next = None
                break
        self._next = next

    def _update(self):
        self._resolve()
        return super(Tristate, self)._update()


class _TristateDriver(_Signal):

    def __init__(self, bus):
        _Signal.__init__(self, bus._val)
        self._val = None
        self._bus = bus

    @_Signal.next.setter
    def next(self, val):
        if isinstance(val, _Signal):
            val = val._val
        if val is None:
            self._next = None
        else:
            self._setNextVal(val)
        _siglist.append(self._bus)


class _DelayedTristate(_DelayedSignal, _Tristate):

    def __init__(self, val, delay=1):
        self._drivers = []
        super(_DelayedTristate, self).__init__(val, delay)
        self._val = None

    def _update(self):
        self._resolve()
        return super(_DelayedTristate, self)._update()
