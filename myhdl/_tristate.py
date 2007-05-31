import warnings

from myhdl._Signal import Signal, DelayedSignal
from myhdl._simulator import _siglist

class BusContentionWarning(UserWarning):
    pass

warnings.filterwarnings('always', r".*", BusContentionWarning)

class Tristate(Signal):
    
    def __new__(cls, val, delay=None):
        """ Return a new TristateBus (default or delay 0) or DelayedTristateBus """
        if delay is not None:
            if delay < 0:
                raise TypeError("Signal: delay should be >= 0")
            return object.__new__(DelayedTristate)
        else:
            return object.__new__(cls)
        
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

    
class DelayedTristate(DelayedSignal, Tristate):

    def __init__(self, val, delay=1):
        self._drivers = []
        super(DelayedTristate, self).__init__(val, delay)
        self._val = None
        
    def _update(self):
        self._resolve()
        return super(DelayedTristate, self)._update()
