from myhdl._Signal import Signal

class _SignalItemProxy(Signal):

    __new__ = object.__new__

    def __init__(self, ref, index):
        self.ref = ref
        self.index = index
        self._eventWaiters = _WaiterList()
        self._posedgeWaiters = _WaiterList()
        self._negedgeWaiters = _WaiterList()

    def _update(self):
        val, next = self.ref.val[self.index], self.ref.next[self.index]
        if val != next:
            waiters = self._eventWaiters[:]
            del self._eventWaiters[:]
            if not val and next:
                waiters.extend(self._posedgeWaiters[:])
                del self._posedgeWaiters[:]
            elif not next and val:
                waiters.extend(self._negedgeWaiters[:])
                del self._negedgeWaiters[:]
            self._val = next
            return waiters
        else:
            return []

    def _get_val(self):
        return self.ref.val[self.index]
    val = property(_get_val, None, None, "'val' access methods")

    def _get_next(self):
        _siglist.append(self)
        return self.ref.next[self.index]
    def _set_next(self, val):
        self.ref.next[self.index] = val
        _siglist.append(self)
    next = property(_get_next, _set_next, None, "'next' access methods")

    


    
