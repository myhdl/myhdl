import warnings

from myhdl._Signal import Signal
from myhdl._simulator import _siglist

class BusContentionWarning(UserWarning):
    pass

warnings.filterwarnings('always', r".*", BusContentionWarning)

class TristateBus(Signal):

    def __init__(self, val):
        self._drivers = []
        Signal.__init__(self, val)
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
        return Signal._update(self)


class _TristateDriver(Signal):
    
    def __init__(self, bus):
        Signal.__init__(self, bus._val)
        self._val = None
        self._bus = bus

    def _set_next(self, val):
         if isinstance(val, Signal):
            val = val._val
         if val is None:
             self._next = None
         else:             
             self._setNextVal(val)
         _siglist.append(self._bus)   
    next = property(Signal._get_next, _set_next, None, "'next' access methods")
    
