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

""" Module with the always_comb function. """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
import inspect
from types import FunctionType
import compiler
from sets import Set

from myhdl import Signal, AlwaysCombError
from myhdl._util import _isGenFunc
from myhdl._cell_deref import _cell_deref

class _error:
    pass
_error.ArgType = "always_comb argument should be a classic function"
_error.NrOfArgs = "always_comb argument should be a function without arguments"
_error.Scope = "always_comb argument should be a local function"
_error.SignalAsInout = "signal used as inout in always_comb function argument"
_error.EmbeddedFunction = "embedded functions in always_comb function argument not supported"
    
def always_comb(func):
    f = inspect.getouterframes(inspect.currentframe())[1][0]
    if not isinstance( func, FunctionType):
        raise AlwaysCombError(_error.ArgType)
    if _isGenFunc(func):
        raise AlwaysCombError(_error.ArgType)
    if func.func_code.co_argcount:
        raise AlwaysCombError(_error.NrOfArgs)
    if func.func_name not in f.f_locals:
        raise AlwaysCombError(_error.Scope)
    varnames = func.func_code.co_varnames
    sigdict = {}
##     for dict in (f.f_locals, f.f_globals):
##         for n, v in dict.items():
##             if isinstance(v, Signal) and \
##                    n not in varnames and \
##                    n not in sigdict:
##                 sigdict[n] = v
    for n, v in func.func_globals.items():
        if isinstance(v, Signal) and \
           n not in varnames:
            sigdict[n] = v
    # handle free variables
    if func.func_code.co_freevars:
        for n, c in zip(func.func_code.co_freevars, func.func_closure):
            obj = _cell_deref(c)
            if isinstance(obj, Signal):
                sigdict[n] = obj
    c = _AlwaysComb(func, sigdict)
    return c
   

INPUT, OUTPUT, INOUT = range(3)

class _SigNameVisitor(object):
    def __init__(self, sigdict):
        self.inputs = Set()
        self.outputs = Set()
        self.toplevel = 1
        self.sigdict = sigdict

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
        if node.name not in self.sigdict:
            return
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
        

class _AlwaysComb(object):

    def __init__(self, func, sigdict):
        self.func = func
        self.sigdict = sigdict
        s = inspect.getsource(func)
        s = s.lstrip()
        tree = compiler.parse(s)
        v = _SigNameVisitor(sigdict)
        compiler.walk(tree, v)
        self.inputs = v.inputs
        self.outputs = v.outputs
        self.senslist = tuple([self.sigdict[n] for n in self.inputs])
        self.gen = self.genfunc()

    def genfunc(self):
        senslist = self.senslist
        func = self.func
        while 1:
            func()
            yield senslist
 
