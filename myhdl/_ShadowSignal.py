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

from myhdl._Signal import _Signal
from myhdl._Waiter import _SignalWaiter, _SignalTupleWaiter
from myhdl._intbv import intbv

# shadow signals
        
        
class _ShadowSignal(_Signal):

    __slots__ = ('gen', 'waiter')

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
            self.gen = self.genfuncIndex()
        else:
            self.gen = self.genfuncSlice()
        self.waiter = _SignalWaiter(self.gen)

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
        self.gen = self.genfunc()
        self.waiter = _SignalTupleWaiter(self.gen)

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

