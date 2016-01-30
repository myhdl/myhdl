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

from myhdl import InstanceError
from myhdl._util import _isGenFunc, _makeAST
from myhdl._Waiter import _inferWaiter

class _error:
    pass
_error.NrOfArgs = "decorated generator function should not have arguments"
_error.ArgType = "decorated object should be a generator function"


def instance(genfunc):
    if not isinstance(genfunc, FunctionType):
        raise InstanceError(_error.ArgType)
    if not _isGenFunc(genfunc):
        raise InstanceError(_error.ArgType)
    if genfunc.__code__.co_argcount > 0:
        raise InstanceError(_error.NrOfArgs)
    return _Instantiator(genfunc)

class _Instantiator(object):

    def __init__(self, genfunc):
        self.genfunc = genfunc
        self.gen = genfunc()
        # infer symdict
        f = self.funcobj
        varnames = f.__code__.co_varnames
        symdict = {}
        for n, v in f.__globals__.items():
            if n not in varnames:
                symdict[n] = v
        # handle free variables
        freevars = f.__code__.co_freevars
        if freevars:
            closure = (c.cell_contents for c in f.__closure__)
            symdict.update(zip(freevars, closure))
        self.symdict = symdict

    @property
    def funcobj(self):
        return self.genfunc

    @property
    def waiter(self):
        return self._waiter()(self.gen)

    def _waiter(self):
        return _inferWaiter

    @property
    def ast(self):
        return _makeAST(self.gen.gi_frame)
