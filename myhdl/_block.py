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

""" Block with the @block decorator function. """
from __future__ import absolute_import, print_function

import inspect

#from functools import wraps
import functools

import myhdl
from myhdl._compat import PY2
from myhdl import BlockError, BlockInstanceError, Cosimulation
from myhdl._instance import _Instantiator
from myhdl._util import _flatten
from myhdl._extractHierarchy import (_makeMemInfo,
                                     _UserVerilogCode, _UserVhdlCode,
                                     _UserVerilogInstance, _UserVhdlInstance)
from myhdl._Signal import _Signal, _isListOfSigs

from weakref import WeakValueDictionary

class _error:
    pass
_error.ArgType = "%s: A block should return block or instantiator objects"
_error.InstanceError = "%s: subblock %s should be encapsulated in a block decorator"


class _CallInfo(object):

    def __init__(self, name, modctxt, symdict):
        self.name = name
        self.modctxt = modctxt
        self.symdict = symdict


def _getCallInfo():
    """Get info on the caller of a BlockInstance.

    A BlockInstance should be used in a block context.
    This function gets the required info from the caller
    It uses the frame stack:
    0: this function
    1: block instance constructor
    2: the decorator function call
    3: the function that defines instances
    4: the caller of the block function, e.g. a BlockInstance.

    """

    stack = inspect.stack()
    # caller may be undefined if instantiation from a Python module
    callerrec = None
    funcrec = stack[3]
    name = funcrec[3]
    if len(stack) > 4:
        callerrec = stack[4]
    # special case for list comprehension's extra scope in PY3
    if name == '<listcomp>':
        if not PY2:
            funcrec = stack[4]
            if len(stack) > 5:
                callerrec = stack[5]

    name = funcrec[3]
    frame = funcrec[0]
    symdict = dict(frame.f_globals)
    symdict.update(frame.f_locals)
    modctxt = False
    if callerrec is not None:
        f_locals = callerrec[0].f_locals
        if 'self' in f_locals:
            modctxt = isinstance(f_locals['self'], _Block)
    return _CallInfo(name, modctxt, symdict)


### I don't think this is the right place for uniqueifying the name.
### This seems to me to be a conversion concern, not a block concern, and
### there should not be the corresponding global state to be maintained here.
### The name should be whatever it is, which is then uniqueified at
### conversion time. Perhaps this happens already (FIXME - check and fix)
### ~ H Gomersall 24/11/2017
_inst_name_set = set()
_name_set = set()

def _uniqueify_name(proposed_name):
    '''Creates a unique block name from the proposed name by appending
    a suitable number to the end. Every name this function returns is
    assumed to be used, so will not be returned again.
    '''
    n = 0

    while proposed_name in _name_set:
        proposed_name = proposed_name + '_' + str(n)
        n += 1

    _name_set.add(proposed_name)

    return proposed_name


class _bound_function_wrapper(object):

    def __init__(self, bound_func, srcfile, srcline):
        self.srcfile = srcfile
        self.srcline = srcline
        self.bound_func = bound_func
        functools.update_wrapper(self, bound_func)
        self.calls = 0
        # register the block
        myhdl._simulator._blocks.append(self)

        self.name_prefix = None
        self.name = None

    def __call__(self, *args, **kwargs):

        name = (
            self.name_prefix + '_' + self.bound_func.__name__ +
            str(self.calls))

        self.calls += 1

        # See concerns above about uniqueifying
        name = _uniqueify_name(name)

        return _Block(self.bound_func, self, name, self.srcfile,
                      self.srcline, *args, **kwargs)

class block(object):

    def __init__(self, func):
        self.srcfile = inspect.getsourcefile(func)
        self.srcline = inspect.getsourcelines(func)[0]
        self.func = func
        functools.update_wrapper(self, func)
        self.calls = 0
        self.name = None

        # register the block
        myhdl._simulator._blocks.append(self)

        self.bound_functions = WeakValueDictionary()

    def __get__(self, instance, owner):
        bound_key = (id(instance), id(owner))

        if bound_key not in self.bound_functions:
            bound_func = self.func.__get__(instance, owner)
            function_wrapper = _bound_function_wrapper(
                bound_func, self.srcfile, self.srcline)
            self.bound_functions[bound_key] = function_wrapper

            proposed_inst_name = owner.__name__ + '0'

            n = 1
            while proposed_inst_name in _inst_name_set:
                proposed_inst_name = owner.__name__ + str(n)
                n += 1

            function_wrapper.name_prefix = proposed_inst_name
            _inst_name_set.add(proposed_inst_name)

        else:
            function_wrapper = self.bound_functions[bound_key]
            bound_func = self.bound_functions[bound_key]

        return function_wrapper

    def __call__(self, *args, **kwargs):

        name = self.func.__name__ + str(self.calls)
        self.calls += 1

        # See concerns above about uniqueifying
        name = _uniqueify_name(name)

        return _Block(self.func, self, name, self.srcfile,
                      self.srcline, *args, **kwargs)


class _Block(object):

    def __init__(self, func, deco, name, srcfile, srcline, *args, **kwargs):
        calls = deco.calls

        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.__doc__ = func.__doc__
        callinfo = _getCallInfo()
        self.callinfo = callinfo
        self.modctxt = callinfo.modctxt
        self.callername = callinfo.name
        self.symdict = None
        self.sigdict = {}
        self.memdict = {}
        self.name = self.__name__ = name

        # flatten, but keep BlockInstance objects
        self.subs = _flatten(func(*args, **kwargs))
        self._verifySubs()
        self._updateNamespaces()
        self.verilog_code = self.vhdl_code = None
        self.sim = None
        if hasattr(deco, 'verilog_code'):
            self.verilog_code = _UserVerilogCode(deco.verilog_code, self.symdict, func.__name__,
                                                 func, srcfile, srcline)
        if hasattr(deco, 'vhdl_code'):
            self.vhdl_code = _UserVhdlCode(deco.vhdl_code, self.symdict, func.__name__,
                                           func, srcfile, srcline)
        if hasattr(deco, 'verilog_instance'):
            self.verilog_code = _UserVerilogInstance(deco.vhdl_instance, self.symdict, func.__name__,
                                                     func, srcfile, srcline)
        if hasattr(deco, 'vhdl_instance'):
            self.vhdl_code = _UserVhdlInstance(deco.vhdl_instance, self.symdict, func.__name__,
                                               func, srcfile, srcline)
        self._config_sim = {'trace': False}

    def _verifySubs(self):
        for inst in self.subs:
            if not isinstance(inst, (_Block, _Instantiator, Cosimulation)):
                raise BlockError(_error.ArgType % (self.name,))
            if isinstance(inst, (_Block, _Instantiator)):
                if not inst.modctxt:
                    raise BlockError(_error.InstanceError % (self.name, inst.callername))

    def _updateNamespaces(self):
        # dicts to keep track of objects used in Instantiator objects
        usedsigdict = {}
        usedlosdict = {}
        for inst in self.subs:
            # the symdict of a block instance is defined by
            # the call context of its instantiations
            if isinstance(inst, Cosimulation):
                continue  # ignore
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

    def _inferInterface(self):
        from myhdl.conversion._analyze import _analyzeTopFunc
        intf = _analyzeTopFunc(self.func, *self.args, **self.kwargs)
        self.argnames = intf.argnames
        self.argdict = intf.argdict

    # Public methods
    # The puropse now is to define the API, optimizations later

    def  _clear(self):
        """ Clear a number of 'global' attributes.
        This is a workaround function for cleaning up before converts.
        """
        # workaround: elaborate again for the side effect on signal attibutes
        self.func(*self.args, **self.kwargs)
        # reset number of calls in all blocks
        for b in myhdl._simulator._blocks:
            b.calls = 0

    def verify_convert(self):
        self._clear()
        return myhdl.conversion.verify(self)

    def analyze_convert(self):
        self._clear()
        return myhdl.conversion.analyze(self)

    def convert(self, hdl='Verilog', **kwargs):
        """Converts this BlockInstance to another HDL

        Args:
            hdl (Optional[str]): Target HDL. Defaults to Verilog
            path (Optional[str]): Destination folder. Defaults to current
                working dir.
            name (Optional[str]): Module and output file name. Defaults to
                `self.mod.__name__`
            trace(Optional[bool]): Verilog only. Whether the testbench should
                dump all signal waveforms. Defaults to False.
            testbench (Optional[bool]): Verilog only. Specifies whether a
                testbench should be created. Defaults to True.
            timescale(Optional[str]): Verilog only. Defaults to '1ns/10ps'
        """

        self._clear()

        if hdl.lower() == 'vhdl':
            converter = myhdl.conversion._toVHDL.toVHDL
        elif hdl.lower() == 'verilog':
            converter = myhdl.conversion._toVerilog.toVerilog
        else:
            raise BlockInstanceError('unknown hdl %s' % hdl)

        conv_attrs = {}
        if 'name' in kwargs:
            conv_attrs['name'] = kwargs.pop('name')
        conv_attrs['directory'] = kwargs.pop('path', '')
        if hdl.lower() == 'verilog':
            conv_attrs['no_testbench'] = not kwargs.pop('testbench', True)
            conv_attrs['timescale'] = kwargs.pop('timescale', '1ns/10ps')
            conv_attrs['trace'] = kwargs.pop('trace', False)
        conv_attrs.update(kwargs)
        for k, v in conv_attrs.items():
            setattr(converter, k, v)
        return converter(self)

    def config_sim(self, trace=False, **kwargs) :
        self._config_sim['trace'] = trace
        if trace:
            for k, v in kwargs.items() :
                setattr(myhdl.traceSignals, k, v)
            myhdl.traceSignals(self)

    def run_sim(self, duration=None, quiet=0):
        if self.sim is None:
            sim = self
            #if self._config_sim['trace']:
            #    sim = myhdl.traceSignals(self)
            self.sim = myhdl._Simulation.Simulation(sim)
        self.sim.run(duration, quiet)

    def quit_sim(self):
        if self.sim is not None:
            self.sim.quit()
