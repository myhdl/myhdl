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


_schedule = _futureEvents.append

class _WaiterList(list):
    pass

def posedge(sig):
    return sig.posedge

def negedge(sig):
    return sig.negedge

class Signal(object):

    __slots__ = ('_next', '_val',
                 '_eventWaiters', '_posedgeWaiters', '_negedgeWaiters',
                )

    def __new__(cls, val, delay=0):
        if delay:
            return object.__new__(DelayedSignal)
        else:
            return object.__new__(cls)

    def __init__(self, val):
        self._next = self._val = val
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


class DelayedSignal(Signal):
    
    __slots__ = ('_nextZ', '_delay', '_timeStamp',
                )

    def __init__(self, val, delay):
        Signal.__init__(self, val)
        self._nextZ = val
        self._delay = delay
        self._timeStamp = 0

    def _update(self):
        if self._next != self._nextZ:
            self._timeStamp = _simulator._time
            # print "Update timestamp %s" % now()
        self._nextZ = self._next
        t = _simulator._time + self._delay
        _schedule((t, _SignalWrap(self, self._next, self._timeStamp)))
        return []

    def _apply(self, next, timeStamp):
        # print "Apply %s %s %s" % (now(), timeStamp, self._timeStamp)
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

   
