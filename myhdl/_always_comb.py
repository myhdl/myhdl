#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2009 Jan Decaluwe
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

""" Module with the always_comb function. """
from __future__ import absolute_import

from types import FunctionType

from myhdl import AlwaysCombError
from myhdl._Signal import _Signal, _isListOfSigs
from myhdl._util import _isGenFunc
from myhdl._instance import _getCallInfo
from myhdl._always import _Always


class _error:
    pass
_error.ArgType = "always_comb argument should be a classic function"
_error.NrOfArgs = "always_comb argument should be a function without arguments"
_error.Scope = "always_comb argument should be a local function"
_error.SignalAsInout = "signal (%s) used as inout in always_comb function argument"
_error.EmbeddedFunction = "embedded functions in always_comb function argument not supported"
_error.EmptySensitivityList = "sensitivity list is empty"


def always_comb(func):
    callinfo = _getCallInfo()
    if not isinstance(func, FunctionType):
        raise AlwaysCombError(_error.ArgType)
    if _isGenFunc(func):
        raise AlwaysCombError(_error.ArgType)
    if func.__code__.co_argcount > 0:
        raise AlwaysCombError(_error.NrOfArgs)
    c = _AlwaysComb(func, callinfo=callinfo)
    return c


class _AlwaysComb(_Always):

    def __init__(self, func, callinfo):
        senslist = []
        super(_AlwaysComb, self).__init__(func, senslist, callinfo=callinfo)

        inouts = self.inouts | self.inputs.intersection(self.outputs)
        if inouts:
            raise AlwaysCombError(_error.SignalAsInout % inouts)

        if self.embedded_func:
            raise AlwaysCombError(_error.EmbeddedFunction)

        for n in self.inputs:
            s = self.symdict[n]
            if isinstance(s, _Signal):
                senslist.append(s)
            elif _isListOfSigs(s):
                senslist.extend(s)
        self.senslist = tuple(senslist)
        if len(self.senslist) == 0:
            raise AlwaysCombError(_error.EmptySensitivityList)

    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        func = self.func
        while 1:
            func()
            yield senslist
