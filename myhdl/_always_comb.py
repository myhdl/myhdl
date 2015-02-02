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

import sys
import inspect
from types import FunctionType
import re
import ast

from myhdl import AlwaysCombError
from myhdl._Signal import _Signal, _isListOfSigs
from myhdl._util import _isGenFunc, _dedent
from myhdl._cell_deref import _cell_deref
from myhdl._Waiter import _Waiter, _SignalWaiter, _SignalTupleWaiter
from myhdl._instance import _Instantiator
from myhdl._resolverefs import _AttrRefTransformer

class _error:
    pass
_error.ArgType = "always_comb argument should be a classic function"
_error.NrOfArgs = "always_comb argument should be a function without arguments"
_error.Scope = "always_comb argument should be a local function"
_error.SignalAsInout = "signal (%s) used as inout in always_comb function argument"
_error.EmbeddedFunction = "embedded functions in always_comb function argument not supported"
_error.EmptySensitivityList= "sensitivity list is empty"

def always_comb(func):
    if not isinstance( func, FunctionType):
        raise AlwaysCombError(_error.ArgType)
    if _isGenFunc(func):
        raise AlwaysCombError(_error.ArgType)
    if func.__code__.co_argcount > 0:
        raise AlwaysCombError(_error.NrOfArgs)
    varnames = func.__code__.co_varnames
    symdict = {}
    for n, v in func.__globals__.items():
        if n not in varnames:
            symdict[n] = v
    # handle free variables
    if func.__code__.co_freevars:
        for n, c in zip(func.__code__.co_freevars, func.__closure__):
            try:
                obj = _cell_deref(c)
                symdict[n] = obj
            except NameError:
                raise NameError(n)
    c = _AlwaysComb(func, symdict)
    return c


INPUT, OUTPUT, INOUT = range(3)



class _SigNameVisitor(ast.NodeVisitor):
    def __init__(self, symdict):
        self.inputs = set()
        self.outputs = set()
        self.toplevel = 1
        self.symdict = symdict
        self.context = INPUT

    def visit_Module(self, node):
        inputs = self.inputs
        outputs = self.outputs
        for n in node.body:
            self.visit(n)
        for n in inputs:
            if n in outputs:
                raise AlwaysCombError(_error.SignalAsInout % n)

    def visit_FunctionDef(self, node):
        if self.toplevel:
            self.toplevel = 0 # skip embedded functions
            for n in node.body:
                self.visit(n)
        else:
            raise AlwaysCombError(_error.EmbeddedFunction)

    def visit_If(self, node):
        if not node.orelse:
            if isinstance(node.test, ast.Name) and \
               node.test.id == '__debug__':
                return # skip
        self.generic_visit(node)

    def visit_Name(self, node):
        id = node.id
        if id not in self.symdict:
            return
        s = self.symdict[id]
        if isinstance(s, _Signal) or _isListOfSigs(s):
            if self.context == INPUT:
                self.inputs.add(id)
            elif self.context == OUTPUT:
                self.outputs.add(id)
            elif self.context == INOUT:
                raise AlwaysCombError(_error.SignalAsInout % id)
            else:
                raise AssertionError("bug in always_comb")

    def visit_Assign(self, node):
        self.context = OUTPUT
        for n in node.targets:
            self.visit(n)
        self.context = INPUT
        self.visit(node.value)

    def visit_Attribute(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        fn = None
        if isinstance(node.func, ast.Name):
            fn = node.func.id
        if fn == "len":
            pass
        else:
            self.generic_visit(node)
            

    def visit_Subscript(self, node, access=INPUT):
        self.visit(node.value)
        self.context = INPUT
        self.visit(node.slice)

    def visit_AugAssign(self, node, access=INPUT):
        self.context = INOUT
        self.visit(node.target)
        self.context = INPUT
        self.visit(node.value)

    def visit_ClassDef(self, node):
        pass # skip

    def visit_Exec(self, node):
        pass # skip

    def visit_Print(self, node):
        pass # skip



class _AlwaysComb(_Instantiator):

#     def __init__(self, func, symdict):
#         self.func = func
#         self.symdict = symdict
#         s = inspect.getsource(func)
#         # remove decorators
#         s = re.sub(r"@.*", "", s)
#         s = s.lstrip()
#         tree = compiler.parse(s)
#         v = _SigNameVisitor(symdict)
#         compiler.walk(tree, v)
#         self.inputs = v.inputs
#         self.outputs = v.outputs
#         senslist = []
#         for n in self.inputs:
#             s = self.symdict[n]
#             if isinstance(s, Signal):
#                 senslist.append(s)
#             else: # list of sigs
#                 senslist.extend(s)
#         self.senslist = tuple(senslist)
#         self.gen = self.genfunc()
#         if len(self.senslist) == 0:
#             raise AlwaysCombError(_error.EmptySensitivityList)
#         if len(self.senslist) == 1:
#             W = _SignalWaiter
#         else:
#             W = _SignalTupleWaiter
#         self.waiter = W(self.gen)

    def __init__(self, func, symdict):
        self.func = func
        self.symdict = symdict
        s = inspect.getsource(func)
        s = _dedent(s)
        tree = ast.parse(s)
        # print ast.dump(tree)
        v = _AttrRefTransformer(self)
        v.visit(tree)
        v = _SigNameVisitor(self.symdict)
        v.visit(tree)
        self.inputs = v.inputs
        self.outputs = v.outputs
        senslist = []
        for n in self.inputs:
            s = self.symdict[n]
            if isinstance(s, _Signal):
                senslist.append(s)
            else: # list of sigs
                senslist.extend(s)
        self.senslist = tuple(senslist)
        self.gen = self.genfunc()
        if len(self.senslist) == 0:
            raise AlwaysCombError(_error.EmptySensitivityList)
        if len(self.senslist) == 1:
            W = _SignalWaiter
        else:
            W = _SignalTupleWaiter
        self.waiter = W(self.gen)



    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        func = self.func
        while 1:
            func()
            yield senslist




