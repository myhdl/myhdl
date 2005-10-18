#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module that provides the Signal class and related objects.

This module provides the following objects:

Signal -- class to model hardware signals
posedge -- callable to model a rising edge on a signal in a yield statement
negedge -- callable to model a falling edge on a signal in a yield statement

"""
__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from inspect import currentframe, getouterframes
from copy import deepcopy as copy

from myhdl import _simulator as sim
from myhdl._simulator import _siglist, _futureEvents, now
from myhdl._intbv import intbv
from myhdl._bin import bin

_schedule = _futureEvents.append
        
       
class _WaiterList(list):

    def purge(self):
        if self:
            self[:] = [w for w in self if not w.hasRun]


class _PosedgeWaiterList(_WaiterList):
    def __init__(self, sig):
        self.sig = sig
    def _toVerilog(self):
        return "posedge %s" % self.sig._name
    
class _NegedgeWaiterList(_WaiterList):
    def __init__(self, sig):
        self.sig = sig
    def _toVerilog(self):
        return "negedge %s" % self.sig._name


def posedge(sig):
    """ Return a posedge trigger object """
    return sig.posedge

def negedge(sig):
    """ Return a negedge trigger object """
    return sig.negedge

class Signal(object):

    """ Signal class.

    Properties:
    val -- current value (read-only)
    next -- next value (read-write)

    """

    __slots__ = ('_next', '_val', '_min', '_max', '_type', 
                 '_eventWaiters', '_posedgeWaiters', '_negedgeWaiters',
                 '_code', '_tracing', '_nrbits', '_checkVal', '_setNextVal',
                 '_printVcd', '_driven' ,'_read', '_name'
                )

    def __new__(cls, val=None, delay=None):
        """ Return a new Signal (default or delay 0) or DelayedSignal """
        if delay is not None:
            if delay < 0:
                raise TypeError("Signal: delay should be >= 0")
            return object.__new__(DelayedSignal)
        else:
            return object.__new__(cls)

    def __init__(self, val=None):
        """ Construct a signal.

        val -- initial value
        
        """
        self._next = self._val = val
        self._min = self._max = None
        self._name = self._read = self._driven = None
        self._nrbits = 0
        self._printVcd = self._printVcdStr
        if isinstance(val, bool):
            self._type = bool
            self._setNextVal = self._setNextBool
            self._printVcd = self._printVcdBit
            self._nrbits = 1
        elif isinstance(val, (int, long)):
            self._type = (int, long)
            self._setNextVal = self._setNextInt
        elif isinstance(val, intbv):
            self._type = intbv
            self._min = val._min
            self._max = val._max
            self._nrbits = val._nrbits
            self._setNextVal = self._setNextIntbv
            if self._nrbits:
                self._printVcd = self._printVcdVec
            else:
                self._printVcd = self._printVcdHex
        elif val is None:
            self._type = None
            self._setNextVal = self._setNext
        else:
            self._type = type(val)
            self._setNextVal = self._setNextType
            if hasattr(val, '_nrbits'):
                self._nrbits = val._nrbits
        self._eventWaiters = _WaiterList()
        self._posedgeWaiters = _PosedgeWaiterList(self)
        self._negedgeWaiters = _NegedgeWaiterList(self)
        self._code = ""
        self._tracing = 0
        
    def _update(self):
        val, next = self._val, self._next
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
            if self._tracing:
                self._printVcd()
            return waiters
        else:
            return []

    # support for the 'val' attribute
    def _get_val(self):
        return self._val
    val = property(_get_val, None, None, "'val' access methods")

    # support for the 'next' attribute
    def _get_next(self):
        if self._next is self._val:
            self._next = copy(self._val)
        _siglist.append(self)
        return self._next
    def _set_next(self, val):
        if isinstance(val, Signal):
            val = val._val
        self._setNextVal(val)
        _siglist.append(self)
    next = property(_get_next, _set_next, None, "'next' access methods")

    # support for the 'posedge' attribute
    def _get_posedge(self):
        return self._posedgeWaiters
    posedge = property(_get_posedge, None, None, "'posedge' access methods")
                       
    # support for the 'negedge' attribute
    def _get_negedge(self):
        return self._negedgeWaiters
    negedge = property(_get_negedge, None, None, "'negedge' access methods")
    
    # support for the 'min' and 'max' attribute
    def _get_max(self):
        return self._max
    max = property(_get_max, None)
    def _get_min(self):
        return self._min
    min = property(_get_min, None)

    # set next methods
    def _setNextBool(self, val):
        if not val in (0, 1):
            raise ValueError("Expected value 0 or 1, got %s" % val)
        self._next = val

    def _setNextInt(self, val):
        if not isinstance(val, (int, long, intbv)):
            raise TypeError("Expected int or intbv, got %s" % type(val))
        self._next = val

    def _setNextIntbv(self, val):
        if isinstance(val, intbv):
            val = val._val
        elif not isinstance(val, (int, long)):
            raise TypeError("Expected int or intbv, got %s" % type(val))
        if self._next is self._val:
            self._next = copy(self._val)
        self._next._val = val
        self._next._checkBounds()

    def _setNextType(self, val):
        if not isinstance(val, self._type):
            raise TypeError("Expected %s, got %s" % (self._type, type(val)))
        self._next = val
        
    def _setNext(self, val):
        self._next = val

    # vcd print methods
    def _printVcdStr(self):
        print >> sim._tf, "s%s %s" % (str(self._val), self._code)
        
    def _printVcdHex(self):
        print >> sim._tf, "s%s %s" % (hex(self._val), self._code)

    def _printVcdBit(self):
        print >> sim._tf, "%d%s" % (self._val, self._code)

    def _printVcdVec(self):
        print >> sim._tf, "b%s %s" % (bin(self._val, self._nrbits), self._code)

    ### operators for which delegation to current value is appropriate ###
        
    # hashing (?)
    def __hash__(self):
        return hash(self._val)
        
    
    def __nonzero__(self):
        if self._val:
            return 1
        else:
            return 0

    # length
    def __len__(self):
        return len(self._val)

    # indexing and slicing methods

    def __getitem__(self, key):
        return self._val[key]
        
    # integer-like methods

    def __add__(self, other):
        if isinstance(other, Signal):
            return self._val + other._val
        else:
            return self._val + other
    def __radd__(self, other):
        return other + self._val
    
    def __sub__(self, other):
        if isinstance(other, Signal):
            return self._val - other._val
        else:
            return self._val - other
    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if isinstance(other, Signal):
            return self._val * other._val
        else:
            return self._val * other
    def __rmul__(self, other):
        return other * self._val

    def __div__(self, other):
        if isinstance(other, Signal):
            return self._val / other._val
        else:
            return self._val / other
    def __rdiv__(self, other):
        return other / self._val
    
    def __truediv__(self, other):
        if isinstance(other, Signal):
            return operator.truediv(self._val, other._val)
        else:
            return operator.truediv(self._val, other)
    def __rtruediv__(self, other):
        return operator.truediv(other, self._val)
    
    def __floordiv__(self, other):
        if isinstance(other, Signal):
            return self._val // other._val
        else:
            return self._val // other
    def __rfloordiv__(self, other):
        return other //  self._val
    
    def __mod__(self, other):
        if isinstance(other, Signal):
            return self._val % other._val
        else:
            return self._val % other
    def __rmod__(self, other):
        return other % self._val

    # XXX divmod
    
    def __pow__(self, other):
        if isinstance(other, Signal):
            return self._val ** other._val
        else:
            return self._val ** other
    def __rpow__(self, other):
        return other ** self._val

    def __lshift__(self, other):
        if isinstance(other, Signal):
            return self._val << other._val
        else:
            return self._val << other
    def __rlshift__(self, other):
        return other << self._val
            
    def __rshift__(self, other):
        if isinstance(other, Signal):
            return self._val >> other._val
        else:
            return self._val >> other
    def __rrshift__(self, other):
        return other >> self._val
           
    def __and__(self, other):
        if isinstance(other, Signal):
            return self._val & other._val
        else:
            return self._val & other
    def __rand__(self, other):
        return other & self._val

    def __or__(self, other):
        if isinstance(other, Signal):
            return self._val | other._val
        else:
            return self._val | other
    def __ror__(self, other):
        return other | self._val
    
    def __xor__(self, other):
        if isinstance(other, Signal):
            return self._val ^ other._val
        else:
            return self._val ^ other
    def __rxor__(self, other):
        return other ^ self._val
    
    def __neg__(self):
        return -self._val

    def __pos__(self):
        return +self._val

    def __abs__(self):
        return abs(self._val)

    def __invert__(self):
        return ~self._val
        
    # conversions
    
    def __int__(self):
        return int(self._val)
        
    def __long__(self):
        return long(self._val)

    def __float__(self):
        return float(self._val)
    
    def __oct__(self):
        return oct(self._val)
    
    def __hex__(self):
        return hex(self._val)


    # comparison
    def __cmp__(self, other):
        return cmp(self._val, other)

    # representation 
    def __str__(self):
        return str(self._val)

    def __repr__(self):
        return "Signal(" + repr(self._val) + ")"

    def _toVerilog(self):
        return self._name

    # augmented assignment not supported
    def _augm(self):
        raise TypeError, "Signal object doesn't support augmented assignment"

    __iadd__ = __isub__ = __idiv__ = __imul__ = __ipow__ = __imod__ = _augm
    __ior__ = __iand__ = __ixor__ = __irshift__ = __ilshift__ = _augm

    # index and slice assignment not supported
    def __setitem__(self, key, val):
        raise TypeError, "Signal object doesn't support item/slice assignment"


class DelayedSignal(Signal):
    
    __slots__ = ('_nextZ', '_delay', '_timeStamp',
                )

    def __init__(self, val=None, delay=1):
        """ Construct a new DelayedSignal.

        Automatically invoked through the Signal new method.
        val -- initial value
        delay -- non-zero delay value
        """
        Signal.__init__(self, val)
        self._nextZ = val
        self._delay = delay
        self._timeStamp = 0

    def _update(self):
        if self._next != self._nextZ:
            self._timeStamp = sim._time
        self._nextZ = self._next
        t = sim._time + self._delay
        _schedule((t, _SignalWrap(self, self._next, self._timeStamp)))
        return []

    def _apply(self, next, timeStamp):
        val = self._val
        if timeStamp == self._timeStamp and val != next:
            waiters = self._eventWaiters[:]
            del self._eventWaiters[:]
            if not val and next:
                waiters.extend(self._posedgeWaiters[:])
                del self._posedgeWaiters[:]
            elif not next and val:
                waiters.extend(self._negedgeWaiters[:])
                del self._negedgeWaiters[:]
            self._val = copy(next)
            if self._tracing:
                self._printVcd()
            return waiters            
        else:
            return []

   # support for the 'delay' attribute
    def _get_delay(self):
         return self._delay
    def _set_delay(self, delay):
         self._delay = delay
    delay = property(_get_delay, _set_delay, None, "'delay' access methods")

        
class _SignalWrap(object):
    def __init__(self, sig, next, timeStamp):
        self.sig = sig
        self.next = next
        self.timeStamp = timeStamp
    def apply(self):
        return self.sig._apply(self.next, self.timeStamp)

   
