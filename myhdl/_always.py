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

""" Module with the always function. """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
import inspect
from types import FunctionType
import compiler
from sets import Set
import re

from myhdl import AlwaysError
from myhdl._util import _isGenFunc
from myhdl._delay import delay
from myhdl._Signal import Signal, _WaiterList, posedge, negedge
from myhdl._Waiter import _Waiter

class _error:
    pass
_error.ArgType = "function with always decorator should be classic"
_error.NrOfArgs = "function with always decorator should not have arguments"


def always(*args):
    assert len(args) > 0
    for arg in args:
        assert isinstance(arg, (Signal, _WaiterList, delay))
    def _always_decorator(func):
        if not isinstance(func, FunctionType):
            raise AlwaysError(_error.ArgType)
        if _isGenFunc(func):
            raise AlwaysError(_error.ArgType)
        if func.func_code.co_argcount:
            raise AlwaysError(_error.NrOfArgs)
        return _Always(func, args)
    return _always_decorator
        

class _Always(object):

    def __init__(self, func, args):
        self.func = func
        self.senslist = tuple(args)
        self.gen = self.genfunc()
        
        # infer appropriate waiter class
        # first infer base type of arguments
        for t in (Signal, _WaiterList, delay):
            if isinstance(args[0], t):
                bt = t
        for arg in args[1:]:
            if not isinstance(arg, bt):
                bt = None
                break
        # now set waiter class
        W = _Waiter

        self.waiter = W(self.gen)
            

    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        func = self.func
        while 1:
            yield senslist
            func()
 
