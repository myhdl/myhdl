#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
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

""" Module that provides the ShadowSignal classes


"""

import warnings

from myhdl._Signal import _Signal
from myhdl._Waiter import _SignalWaiter, _SignalTupleWaiter
from myhdl._intbv import intbv
from myhdl._simulator import _siglist

# shadow signals
        
        
class _ShadowSignal(_Signal):

    __slots__ = ('waiter')

    def __init__(self, val):
        _Signal.__init__(self, val)
        self.driven = True


        
class _SliceSignal(_ShadowSignal):

    __slots__ = ('sig', 'left', 'right')

    def __init__(self, sig, left, right=None):
        ### XXX error checks
        if right is None:
            _ShadowSignal.__init__(self, sig[left])
        else:
            _ShadowSignal.__init__(self, sig[left:right])
        self.sig = sig
        self.left = left
        self.right = right
        if right is None:
            gen = self.genfuncIndex()
        else:
            gen = self.genfuncSlice()
        self.waiter = _SignalWaiter(gen)

    def genfuncIndex(self):
        sig, index = self.sig, self.left
        set_next = _Signal._set_next
        while 1:
            set_next(self, sig[index])
            yield sig

    def genfuncSlice(self):
        sig, left, right = self.sig, self.left, self.right
        set_next = _Signal._set_next
        while 1:
            set_next(self, sig[left:right])
            yield sig

    def toVerilog(self):
        if self.right is None:
            return "assign %s = %s[%s];" % (self._name, self.sig._name, self.left)
        else:
            return "assign %s = %s[%s-1:%s];" % (self._name, self.sig._name, self.left, self.right)

    def toVHDL(self):
        if self.right is None:
            return "%s <= %s(%s);" % (self._name, self.sig._name, self.left)
        else:
            return "%s <= %s(%s-1 downto %s);" % (self._name, self.sig._name, self.left, self.right)



class ConcatSignal(_ShadowSignal):

    __slots__ = ('_args',)

    def __init__(self, *args):
        assert len(args) >= 2
        self._args = args
        ### XXX error checks
        nrbits = 0
        for a in args:
            nrbits += len(a)
        ini = intbv(0)[nrbits:]
        hi = nrbits
        for a in args:
            lo = hi - len(a)
            ini[hi:lo] = a
            hi = lo
        _ShadowSignal.__init__(self, ini)
        gen = self.genfunc()
        self.waiter = _SignalTupleWaiter(gen)

    def genfunc(self):
        set_next = _Signal._set_next
        args = self._args
        nrbits = self._nrbits
        newval = intbv(0)[nrbits:]
        while 1:
            hi = nrbits
            for a in args:
                lo = hi - len(a)
                newval[hi:lo] = a
                hi = lo
            set_next(self, newval)
            yield args
                

    def toVHDL(self):
        lines = []
        hi = self._nrbits
        for a in self._args:
            lo = hi - len(a)
            if len(a) == 1:
                lines.append("%s(%s) <= %s;" % (self._name, lo, a._name))
            else:
                lines.append("%s(%s-1 downto %s) <= %s;" % (self._name, hi, lo, a._name))
            hi = lo
        return "\n".join(lines)

    def toVerilog(self):
        lines = []
        hi = self._nrbits
        for a in self._args:
            lo = hi - len(a)
            if len(a) == 1:
                lines.append("assign %s[%s] = %s;" % (self._name, lo, a._name))
            else:
                lines.append("assign %s[%s-1:%s] = %s;" % (self._name, hi, lo, a._name))
            hi = lo
        return "\n".join(lines)


# Tristate signal


class BusContentionWarning(UserWarning):
    pass

warnings.filterwarnings('always', r".*", BusContentionWarning)

# def Tristate(val, delay=None):
#     """ Return a new Tristate(default or delay 0) or DelayedTristate """
#     if delay is not None:
#         if delay < 0:
#             raise TypeError("Signal: delay should be >= 0")
#         return _DelayedTristate(val, delay)
#     else:
#         return _Tristate(val)
 
 
def TristateSignal(val):
    return _TristateSignal(val)


class _TristateSignal(_ShadowSignal):

    __slots__ = ('_drivers', '_ini' )
            
    def __init__(self, val):
        self._drivers = []
        _ShadowSignal.__init__(self, val=None)     
        self._ini = val
        self.waiter = _SignalTupleWaiter(self._resolve())

    def driver(self):
        d = _TristateDriver(self)
        self._drivers.append(d)
        return d

    def _resolve(self):
        senslist = self._drivers
        while 1:
            yield senslist
            res = None
            for d in senslist:
                print d
                print res
                if res is None:
                    res = d._val
                elif d._val is not None:
                    warnings.warn("Bus contention", category=BusContentionWarning)
                    res = None
                    break
            self.next = res


class _TristateDriver(_Signal):
    
    def __init__(self, sig):
        _Signal.__init__(self, sig._ini)
        self._val = None
        self._sig = sig

    def _set_next(self, val):
         if isinstance(val, _Signal):
            val = val._val
         if val is None:
             self._next = None
         else:             
             self._setNextVal(val)
         _siglist.append(self)   
         
    # redefine property because standard interitance doesn't work for setter/getter functions
    next = property(_Signal._get_next, _set_next, None, "'next' access methods")
