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

import inspect

import myhdl
from myhdl import ModuleError
from myhdl._instance import _Instantiator
from myhdl._util import _flatten
from myhdl._extractHierarchy import (_MemInfo, _makeMemInfo,
    _UserVerilogCode, _UserVhdlCode)
from myhdl._Signal import _Signal, _isListOfSigs


class _error:
    pass
_error.ArgType = "A module should return module or instantiator objects"
_error.InstanceError = "%s: submodule %s should be encapsulated in a module decorator"

class _CallInfo(object):
    def __init__(self, name, modctxt, symdict):
        self.name = name
        self.modctxt = modctxt
        self.symdict = symdict

def _getCallInfo():
    """Get info on the caller of a ModuleInstance.

    A ModuleInstance should be used in a module context.
    This function gets the required info from the caller
    It uses the frame stack:
    0: this function
    1: module instance constructor
    2: the _Module class __call__()
    3: the function that defines instances
    4: the caller of the module function, e.g. a ModuleInstance.

    There is a complication when the decorator is used in on a method.
    In this case, it is used as a descriptor, and there is an additional
    stack level due to the __get__ method. The current hack is to check
    whether we are still in this Python module at level 3, and increment
    all the subsequent levels.
    """

    stack = inspect.stack()
    # check whether the decorator is used as a descriptor
    if (inspect.getmodule(stack[3][0]) is myhdl._module):
        funcrec = stack[4]
        callerrec = stack[5]
    else:
        funcrec = stack[3]
        callerrec = stack[4]
    name = funcrec[3]
    frame = funcrec[0]
    symdict = dict(frame.f_globals)
    symdict.update(frame.f_locals)
    modctxt = False
    f_locals = callerrec[0].f_locals
    if 'self' in f_locals:
        modctxt = isinstance(f_locals['self'], _ModuleInstance)
    return _CallInfo(name, modctxt, symdict)


def module(modfunc):
    return _Module(modfunc)

class _Module(object):

    def __init__(self, modfunc):
        self.modfunc = modfunc
        self.__name__ = self.name = modfunc.__name__
        self.sourcefile = inspect.getsourcefile(modfunc)
        self.sourceline = inspect.getsourcelines(modfunc)[0]
        self.count = 0

    def __call__(self, *args, **kwargs):
        modinst = _ModuleInstance(self, *args, **kwargs)
        self.count += 1
        return modinst

    # This is the way to make the module decorator work on methods
    # Turn it into a descriptor, used when accessed as an attribute
    # In that case, the object is bound to the call method
    # like done automatically for classic bound methods
    # http://stackoverflow.com/a/3296318/574895
    # Avoid functools to have identical behavior between
    # CPython and PyPy
    def __get__(self, obj, objtype):
        """Support instance methods."""
        def f(*args, **kwargs):
            return self.__call__(obj, *args, **kwargs)
        return f


class _ModuleInstance(object):

    def __init__(self, mod, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.mod = mod
        callinfo = _getCallInfo()
        self.callinfo = callinfo
        self.modctxt = callinfo.modctxt
        self.callername = callinfo.name
        self.symdict = None
        self.sigdict = {}
        self.memdict = {}
        # flatten, but keep ModuleInstance objects
        self.subs = _flatten(mod.modfunc(*args, **kwargs))
        self.verify()
        self.update()
        self.name = self.__name__ = mod.__name__ + '_' + str(mod.count)
        self.verilog_code = self.vhdl_code = None
        if hasattr(mod, 'verilog_code'):
            self.verilog_code = _UserVerilogCode(mod.verilog_code, self.symdict, mod.name,
                                                 mod.modfunc, mod.sourcefile, mod.sourceline)
        if hasattr(mod, 'vhdl_code'):
            self.vhdl_code = _UserVhdlCode(mod.vhdl_code, self.symdict, mod.name,
                                           mod.modfunc, mod.sourcefile, mod.sourceline)

    def verify(self):
        for inst in self.subs:
            # print (inst.name, type(inst))
            if not isinstance(inst, (_ModuleInstance, _Instantiator)):
                raise ModuleError(_error.ArgType)
            if not inst.modctxt:
                raise ModuleError(_error.InstanceError % (self.mod.name, inst.callername))

    def update(self):
        # dicts to keep track of objects used in Instantiator objects
        usedsigdict = {}
        usedlosdict = {}
        for inst in self.subs:
            # the symdict of a module instance is defined by
            # the call context of its instantations
            if self.symdict is None:
                self.symdict = inst.callinfo.symdict
            if isinstance(inst, _Instantiator):
                usedsigdict.update(inst.sigdict)
                usedlosdict.update(inst.losdict)
        if self.symdict is None:
            self.symdict = {}
        # Special case: due to attribute reference transformation, the
        # sigdict and losdict from Instantiator objects may contain new
        # references. Therefore, update the symdict with them.
        # To be revisited.
        self.symdict.update(usedsigdict)
        self.symdict.update(usedlosdict)
        # Infer sigdict and memdict, with compatibility patches from _extractHierarchy
        for n, v in self.symdict.items():
            if isinstance(v, _Signal):
                self.sigdict[n] = v
                if n in usedsigdict:
                    v._markUsed()
            if _isListOfSigs(v):
                m = _makeMemInfo(v)
                self.memdict[n] = m
                if n in usedlosdict:
                    m._used = True

    def inferInterface(self):
        from myhdl.conversion._analyze import _analyzeTopFunc
        intf = _analyzeTopFunc(self.mod.modfunc, *self.args, **self.kwargs)
        self.argnames = intf.argnames
        self.argdict = intf.argdict
