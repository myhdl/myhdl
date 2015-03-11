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

""" Module with the always function. """
from __future__ import absolute_import


from types import FunctionType

from myhdl import AlwaysError
from myhdl._util import _isGenFunc
from myhdl._delay import delay
from myhdl._Signal import _Signal, _WaiterList, posedge, negedge
from myhdl._Waiter import _Waiter, _SignalWaiter, _SignalTupleWaiter, \
                          _DelayWaiter, _EdgeWaiter, _EdgeTupleWaiter
from myhdl._instance import _Instantiator

class _error:
    pass
_error.DecArgType = "decorator argument should be a Signal, edge, or delay"
_error.ArgType = "decorated object should be a classic (non-generator) function"
_error.NrOfArgs = "decorated function should not have arguments"
_error.DecNrOfArgs = "decorator should have arguments"


def always(*args):
    for arg in args:
        if isinstance(arg, _Signal):
            arg._read = True
            arg._used = True
        elif isinstance(arg, _WaiterList):
            arg.sig._read = True
            arg.sig._used = True
        elif not isinstance(arg, delay):
            raise AlwaysError(_error.DecArgType)
    def _always_decorator(func):
        if not isinstance(func, FunctionType):
            raise AlwaysError(_error.ArgType)
        if _isGenFunc(func):
            raise AlwaysError(_error.ArgType)
        if func.__code__.co_argcount > 0:
            raise AlwaysError(_error.NrOfArgs)
        return _Always(func, args)
    return _always_decorator
        

class _Always(_Instantiator):

    def __init__(self, func, args):
        self.func = func
        self.senslist = tuple(args)
        self.gen = self.genfunc()
        
        # infer appropriate waiter class
        # first infer base type of arguments
        for t in (_Signal, _WaiterList, delay):
            if isinstance(args[0], t):
                bt = t
        for arg in args[1:]:
            if not isinstance(arg, bt):
                bt = None
                break
        # now set waiter class

        W = _Waiter
        
        if bt is delay:
            W = _DelayWaiter
        elif len(self.senslist) == 1:
            if bt is _Signal:
                W = _SignalWaiter
            elif bt is _WaiterList:
                W = _EdgeWaiter
        else:
            if bt is _Signal:
                W = _SignalTupleWaiter
            elif bt is _WaiterList:
                W = _EdgeTupleWaiter

        self.waiter = W(self.gen)
            

    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        func = self.func
        while 1:
            yield senslist
            func()
 
