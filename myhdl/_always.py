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
from myhdl._Signal import _Signal
from myhdl._Signal import _WaiterList
from myhdl._Waiter import _Waiter, _SignalWaiter, _SignalTupleWaiter, \
    _DelayWaiter, _EdgeWaiter, _EdgeTupleWaiter
from myhdl._instance import _Instantiator, _getCallInfo


class _error:
    pass
_error.DecArgType = "decorator argument should be a Signal, edge, or delay"
_error.ArgType = "decorated object should be a classic (non-generator) function"
_error.NrOfArgs = "decorated function should not have arguments"
_error.DecNrOfArgs = "decorator should have arguments"


def _get_sigdict(sigs, symdict):
    """Lookup signals in caller namespace and return sigdict

    Lookup signals in then namespace of a caller. This is used to add
    signal arguments from an instantiator decorator to the instance.
    0: this function
    1: the instantiator decorator
    2: the module function that defines instances
    """

    sigdict = {}
    for n, v in symdict.items():
        for s in sigs:
            if s is v:
                sigdict[n] = s
    return sigdict


def always(*args):
    callinfo = _getCallInfo()
    sigargs = []
    for arg in args:
        if isinstance(arg, _Signal):
            arg._read = True
            arg._used = True
            sigargs.append(arg)
        elif isinstance(arg, _WaiterList):
            arg.sig._read = True
            arg.sig._used = True
            sigargs.append(arg.sig)
        elif not isinstance(arg, delay):
            raise AlwaysError(_error.DecArgType)
    sigdict = _get_sigdict(sigargs, callinfo.symdict)

    def _always_decorator(func):
        if not isinstance(func, FunctionType):
            raise AlwaysError(_error.ArgType)
        if _isGenFunc(func):
            raise AlwaysError(_error.ArgType)
        if func.__code__.co_argcount > 0:
            raise AlwaysError(_error.NrOfArgs)
        return _Always(func, args, callinfo=callinfo, sigdict=sigdict)
    return _always_decorator


class _Always(_Instantiator):

    def __init__(self, func, senslist, callinfo, sigdict=None):
        self.func = func
        self.senslist = tuple(senslist)
        super(_Always, self).__init__(self.genfunc, callinfo=callinfo)
        # update sigdict with decorator signal arguments
        if sigdict is not None:
            self.sigdict.update(sigdict)

    @property
    def funcobj(self):
        return self.func

    def _waiter(self):
        # infer appropriate waiter class
        # first infer base type of arguments
        for t in (_Signal, _WaiterList, delay):
            if isinstance(self.senslist[0], t):
                bt = t
        for s in self.senslist[1:]:
            if not isinstance(s, bt):
                bt = None
                break
        # now set waiter class
        w = _Waiter
        if bt is delay:
            w = _DelayWaiter
        elif len(self.senslist) == 1:
            if bt is _Signal:
                w = _SignalWaiter
            elif bt is _WaiterList:
                w = _EdgeWaiter
        else:
            if bt is _Signal:
                w = _SignalTupleWaiter
            elif bt is _WaiterList:
                w = _EdgeTupleWaiter
        return w

    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        func = self.func
        while 1:
            yield senslist
            func()
