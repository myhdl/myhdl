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
__version__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators
from copy import deepcopy as copy

import _simulator
from _simulator import _siglist, _futureEvents, now
from intbv import intbv


_schedule = _futureEvents.append

class _WaiterList(list):
    pass

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

    __slots__ = ('_next', '_val', '_type',
                 '_eventWaiters', '_posedgeWaiters', '_negedgeWaiters',
                )

    def __new__(cls, val, delay=0):
        """ Return a new Signal (default or delay 0) or DelayedSignal """
        if delay:
            return object.__new__(DelayedSignal)
        else:
            return object.__new__(cls)

    def __init__(self, val):
        """ Construct a signal.

        val -- initial value
        
        """
        self._next = self._val = val
        if type(val) in (int, long, intbv):
            self._type = (int, long, intbv)
        else:
            self._type = type(val)
        self._eventWaiters = _WaiterList()
        self._posedgeWaiters = _WaiterList()
        self._negedgeWaiters = _WaiterList()
        
    def _update(self):
        if self._val != self._next:
            waiters = self._eventWaiters[:]
            del self._eventWaiters[:]
            if not self._val and self._next:
                waiters.extend(self._posedgeWaiters[:])
                del self._posedgeWaiters[:]
            elif not self._next and self._val:
                waiters.extend(self._negedgeWaiters[:])
                del self._negedgeWaiters[:]
            self._val = self._next
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
        if not isinstance(val, self._type):
            raise TypeError, "Incompatible type(v) for sig.next = v\n" \
                  "           Expected %s, got %s" % (self._type, type(val))
        self._next = val
        _siglist.append(self)
    next = property(_get_next, _set_next, None, "'next' access methods")

    # support for the 'posedge' attribute
    def _get_posedge(self):
        return self._posedgeWaiters
    posedge = property(_get_posedge, None, None, "'posedge' access methodes")
                       
    # support for the 'negedge' attribute
    def _get_negedge(self):
        return self._negedgeWaiters
    negedge = property(_get_negedge, None, None, "'posedge' access methodes")
    

    # hashing not supported
    def __hash__(self):
        return hash(self._val)
        
    ### operators for which delegation to current value is appropriate ###
    
    def __nonzero__(self):
        if self._val:
            return 1
        else:
            return 0

    # indexing and slicing methods

    def __getitem__(self, i):
        return self._val[i]

    def __getslice__(self, i, j):
        return self._val[i:j]
    
        
    # integer-like methods

    def __add__(self, other):
        if type(other) is Signal:
            return self._val + other._val
        else:
            return self._val + other
    def __radd__(self, other):
        return other + self._val
    
    def __sub__(self, other):
        if type(other) is Signal:
            return self._val - other._val
        else:
            return self._val - other
    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if type(other) is Signal:
            return self._val * other._val
        else:
            return self._val * other
    def __rmul__(self, other):
        return other * self._val

    def __div__(self, other):
        if type(other) is Signal:
            return self._val / other._val
        else:
            return self._val / other
    def __rdiv__(self, other):
        return other / self._val
    
    def __mod__(self, other):
        if type(other) is Signal:
            return self._val % other._val
        else:
            return self._val % other
    def __rmod__(self, other):
        return other % self._val

    # XXX divmod
    
    def __pow__(self, other):
        if type(other) is Signal:
            return self._val ** other._val
        else:
            return self._val ** other
    def __rpow__(self, other):
        return other ** self._val

    def __lshift__(self, other):
        if type(other) is Signal:
            return self._val << other._val
        else:
            return self._val << other
    def __rlshift__(self, other):
        return other << self._val
            
    def __rshift__(self, other):
        if type(other) is Signal:
            return self._val >> other._val
        else:
            return self._val >> other
    def __rrshift__(self, other):
        return other >> self._val
           
    def __and__(self, other):
        if type(other) is Signal:
            return self._val & other._val
        else:
            return self._val & other
    def __rand__(self, other):
        return other & self._val

    def __or__(self, other):
        if type(other) is Signal:
            return self._val | other._val
        else:
            return self._val | other
    def __ror__(self, other):
        return other | self._val
    
    def __xor__(self, other):
        if type(other) is Signal:
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

    # augmented assignment not supported
    def _augm(self):
        raise TypeError, "Signal object doesn't support augmented assignment"

    __iadd__ = __isub__ = __idiv__ = __imul__ = __ipow__ = __imod__ = _augm
    __ior__ = __iand__ = __ixor__ = __irshift__ = __ilshift__ = _augm

    # index and slice assignment not supported
    def __setitem__(self, i, val):
        raise TypeError, "Signal object doesn't support item assignment"

    def __setslice__(self, i, j, val):
        raise TypeError, "Signal object doesn't support slice assignment"


class DelayedSignal(Signal):
    
    __slots__ = ('_nextZ', '_delay', '_timeStamp',
                )

    def __init__(self, val, delay):
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
            self._timeStamp = _simulator._time
        self._nextZ = self._next
        t = _simulator._time + self._delay
        _schedule((t, _SignalWrap(self, self._next, self._timeStamp)))
        return []

    def _apply(self, next, timeStamp):
        if timeStamp == self._timeStamp and self._val != next:
            waiters = self._eventWaiters[:]
            del self._eventWaiters[:]
            if not self._val and next:
                waiters.extend(self._posedgeWaiters[:])
                del self._posedgeWaiters[:]
            elif not next and self._val:
                waiters.extend(self._negedgeWaiters[:])
                del self._negedgeWaiters[:]
            self._val = copy(next)
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

   
