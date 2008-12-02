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

""" Module with the always_comb function. """

import sys
import inspect
from types import FunctionType
import compiler
from sets import Set
import re

from myhdl import Signal, AlwaysCombError
from myhdl._Signal import _isListOfSigs
from myhdl._util import _isGenFunc
from myhdl._cell_deref import _cell_deref
from myhdl._Waiter import _Waiter, _SignalWaiter, _SignalTupleWaiter
from myhdl._instance import _Instantiator

class _error:
    pass
_error.ArgType = "always_comb argument should be a classic function"
_error.NrOfArgs = "always_comb argument should be a function without arguments"
_error.Scope = "always_comb argument should be a local function"
_error.SignalAsInout = "signal used as inout in always_comb function argument"
_error.EmbeddedFunction = "embedded functions in always_comb function argument not supported"
_error.EmptySensitivityList= "sensitivity list is empty"
    
def always_comb(func):
    if not isinstance( func, FunctionType):
        raise AlwaysCombError(_error.ArgType)
    if _isGenFunc(func):
        raise AlwaysCombError(_error.ArgType)
    if func.func_code.co_argcount > 0:
        raise AlwaysCombError(_error.NrOfArgs)
    varnames = func.func_code.co_varnames
    symdict = {}
    for n, v in func.func_globals.items():
        if n not in varnames:
            symdict[n] = v
    # handle free variables
    if func.func_code.co_freevars:
        for n, c in zip(func.func_code.co_freevars, func.func_closure):
            obj = _cell_deref(c)
            symdict[n] = obj
    c = _AlwaysComb(func, symdict)
    return c
   

INPUT, OUTPUT, INOUT = range(3)

class _SigNameVisitor(object):
    def __init__(self, symdict):
        self.inputs = Set()
        self.outputs = Set()
        self.toplevel = 1
        self.symdict = symdict

    def visitModule(self, node):
        inputs = self.inputs
        outputs = self.outputs
        self.visit(node.node)
        for n in inputs:
            if n in outputs:
                raise AlwaysCombError(_error.SignalAsInout)

    def visitFunction(self, node):
        if self.toplevel:
            self.toplevel = 0 # skip embedded functions
            self.visit(node.code)
        else:
            raise AlwaysCombError(_error.EmbeddedFunction)

    def visitIf(self, node):
        if len(node.tests) == 1 and not node.else_:
            test = node.tests[0][0]
            if isinstance(test, compiler.ast.Name) and \
               test.name == '__debug__':
                return # skip
        for n in node.getChildNodes():
            self.visit(n)
            
    def visitName(self, node, access=INPUT):
        if node.name not in self.symdict:
            return
        s = self.symdict[node.name]
        if isinstance(s, Signal) or _isListOfSigs(s):
            if access == INPUT:
                self.inputs.add(node.name)
            elif access == OUTPUT:
                self.outputs.add(node.name)
            elif access == INOUT:
                raise AlwaysCombError(_error.SignalAsInout)
            else:
                raise AlwaysCombError
            
    def visitAssign(self, node, access=OUTPUT):
        for n in node.nodes:
            self.visit(n, OUTPUT)
        self.visit(node.expr, INPUT)

    def visitAssAttr(self, node, access=OUTPUT):
        self.visit(node.expr, OUTPUT)

    def visitSubscript(self, node, access=INPUT):
        self.visit(node.expr, access)
        for n in node.subs:
            self.visit(n, INPUT)

    def visitSlice(self, node, access=INPUT):
        self.visit(node.expr, access)
        if node.lower:
            self.visit(node.lower, INPUT)
        if node.upper:
            self.visit(node.upper, INPUT)

    def visitAugAssign(self, node, access=INPUT):
        self.visit(node.node, INOUT)
        self.visit(node.expr, INPUT)
        
    def visitClass(self, node):
        pass # skip

    def visitExec(self, node):
        pass # skip

    def visitPrintnl(self, node):
        pass # skip
    
    def visitPrint(self, node):
        pass # skip
        

class _AlwaysComb(_Instantiator):

    def __init__(self, func, symdict):
        self.func = func
        self.symdict = symdict
        s = inspect.getsource(func)
        # remove decorators
        s = re.sub(r"@.*", "", s)
        s = s.lstrip()
        tree = compiler.parse(s)
        v = _SigNameVisitor(symdict)
        compiler.walk(tree, v)
        self.inputs = v.inputs
        self.outputs = v.outputs
        senslist = []
        for n in self.inputs:
            s = self.symdict[n]
            if isinstance(s, Signal):
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
 
