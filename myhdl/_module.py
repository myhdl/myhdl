#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2016 Jan Decaluwe
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

""" Module with the @module decorator function. """
from __future__ import absolute_import

import functools
import inspect

from myhdl import ModuleError
from myhdl._instance import _Instantiator
from myhdl._util import _flatten
from myhdl._extractHierarchy import _MemInfo, _makeMemInfo


class _error:
    pass
_error.ArgType = "A module should return module or instantiator objects"
_error.InstanceError = "%s: submodule %s should be encapsulated in a module decorator"

class _CallInfo(object):
    def __init__(self, name, modctxt):
        self.name = name
        self.modctxt = modctxt

def _getCallInfo():
    """Get info on the caller of a module instance.

    For hierarchy extraction, a module instance should only be used
    within a module context. This function gets info from the caller
    to be able to check that. It uses the frame stack:
    0: this function
    1: module instance constructor
    2: the _Module class __call__()
    3: the function that defines instances
    4: the caller of the module function, e.g. a ModuleInstance.
    """
    name = inspect.stack()[3][3]
    modctxt = False
    f_locals = inspect.stack()[4][0].f_locals
    if 'self' in f_locals:
        modctxt = isinstance(f_locals['self'], _ModuleInstance)
    return _CallInfo(name, modctxt)


def module(modfunc):
    return _Module(modfunc)

class _Module(object):

    def __init__(self, modfunc):
        self.modfunc = modfunc
        self.__name__ = self.name = modfunc.__name__
        self.count = 0

    def __call__(self, *args, **kwargs):
        modinst = _ModuleInstance(self, *args, **kwargs)
        self.count += 1
        return modinst

class _ModuleInstance(object):

    def __init__(self, mod, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.mod = mod
        callinfo = _getCallInfo()
        self.modctxt = callinfo.modctxt
        # this is the name of the instance caller
        self.callername = callinfo.name
        self.sigdict = {}
        self.memdict = {}
        # flatten, but keep ModuleInstance objects
        self.subs = _flatten(mod.modfunc(*args, **kwargs))
        self.verifyMod()
        self.updateMod()
        # self.inferInterface(*args, **kwargs)
        self.name = self.__name__ = mod.__name__ + '_' + str(mod.count)

    def verifyMod(self):
        for inst in self.subs:
            # print (inst.name, type(inst))
            if not isinstance(inst, (_ModuleInstance, _Instantiator)):
                raise ModuleError(_error.ArgType)
            if not inst.modctxt:
                raise ModuleError(_error.InstanceError % (self.mod.name, inst.callername))

    def updateMod(self):
        losdict = {}
        for inst in self.subs:
            if isinstance(inst, _Instantiator):
                self.sigdict.update(inst.sigdict)
                losdict.update(inst.losdict)
        # compatibility patches from _extractHierarchy
        for s in self.sigdict.values():
            s._markUsed()
        for n, l in losdict.items():
            m = _makeMemInfo(l)
            self.memdict[n] = m
            m._used = True

    def inferInterface(self):
        from myhdl.conversion._analyze import _analyzeTopFunc
        intf = _analyzeTopFunc(self.mod.modfunc, *self.args, **self.kwargs)
        self.argnames = intf.argnames
        self.argdict = intf.argdict
