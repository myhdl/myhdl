#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2012 Jan Decaluwe
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

""" Module with the always_ff decorator. """


import sys
import inspect
from types import FunctionType
import ast

from myhdl import AlwaysError
from myhdl._util import _isGenFunc, _dedent
from myhdl._cell_deref import _cell_deref
from myhdl._delay import delay
from myhdl._Signal import _Signal, _WaiterList,_isListOfSigs
from myhdl._Waiter import _Waiter, _EdgeWaiter, _EdgeTupleWaiter
from myhdl._instance import _Instantiator

# evacuate this later
AlwaysFFError = AlwaysError

class _error:
    pass
_error.EdgeType = "first argument should be an edge"
_error.ResetType = "reset argument should be a signal"
_error.ArgType = "decorated object should be a classic (non-generator) function"
_error.NrOfArgs = "decorated function should not have arguments"
_error.SigAugAssign = "signal assignment does not support augmented assignment"
_error.EmbeddedFunction = "embedded functions in always_ff function not supported"

def always_ff(edge, reset=False, level=0, async=True):
    if not isinstance(edge, _WaiterList):
        raise AlwaysFFError(_error.EdgeType)
    edge.sig._read = True
    edge.sig._used = True
    if reset is not None:
        if not isinstance(reset, _Signal):
            raise AlwaysFFError(_error.ResetType)
    reset._read = True
    reset._used = True

    def _always_ff_decorator(func):
        if not isinstance(func, FunctionType):
            raise AlwaysFFError(_error.ArgType)
        if _isGenFunc(func):
            raise AlwaysFFError(_error.ArgType)
        if func.func_code.co_argcount > 0:
            raise AlwaysFFError(_error.NrOfArgs)
        return _AlwaysFF(func, edge, reset, level, async)
    return _always_ff_decorator
        

class _AlwaysFF(_Instantiator):

    def __init__(self, func, edge, reset, level, async):
        self.func = func
        self.reset = reset
        self.level = level
        senslist = [edge]
        if async:
            if level:
                senslist.append(reset.posedge)
            else:
                senslist.append(reset.negedge)
        self.senslist = senslist
        if reset is not None:
            self.gen = self.genfunc()
        else:
            self.gen = self.genfunc_no_reset()
        if len(self.senslist) == 1:
            W = _EdgeWaiter
        else:
            W = _EdgeTupleWaiter
        self.waiter = W(self.gen)

        # find symdict
        # similar to always_comb, but in class constructor
        varnames = func.func_code.co_varnames
        symdict = {}
        for n, v in func.func_globals.items():
            if n not in varnames:
                symdict[n] = v
        # handle free variables
        if func.func_code.co_freevars:
            for n, c in zip(func.func_code.co_freevars, func.func_closure):
                try:
                    obj = _cell_deref(c)
                    symdict[n] = obj
                except NameError:
                    raise NameError(n)
        self.symdict = symdict

        # now infer outputs to be reset
        s = inspect.getsource(func)
        s = _dedent(s)
        tree = ast.parse(s)
        # print ast.dump(tree)
        v = _SigNameVisitor(symdict)
        v.visit(tree)
        self.outputs = v.outputs

    def reset_sigs(self):
        for n in self.outputs:
            s = self.symdict[n]
            if isinstance(s, _Signal):
                s.next = s._init
            else:
                print type(s)
                assert _isListOfSigs(s)
                for e in s:
                    e.next = e._init

    def genfunc(self):
        senslist = self.senslist
        if len(senslist) == 1:
            senslist = senslist[0]
        reset_sigs = self.reset_sigs
        func = self.func
        while 1:
            yield senslist
            if self.reset == self.level:
                reset_sigs()
            else:
                func()

    def genfunc_no_reset(self):
        senslist = self.senslist
        assert len(senslist) == 1
        func = self.func
        while 1:
            yield senslist
            func()




# similar to always_comb, calls for refactoring
# note: make a difference between augmented assign and inout signals

INPUT, OUTPUT, INOUT = range(3)

class _SigNameVisitor(ast.NodeVisitor):
    def __init__(self, symdict):
        self.inputs = set()
        self.outputs = set()
        self.toplevel = 1
        self.symdict = symdict
        self.context = INPUT

    def visit_Module(self, node):

        for n in node.body:
            self.visit(n)

    def visit_FunctionDef(self, node):
        if self.toplevel:
            self.toplevel = 0 # skip embedded functions
            for n in node.body:
                self.visit(n)
        else:
            raise AlwaysFFError(_error.EmbeddedFunction)

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
                raise AlwaysFFError(_error.SigAugAssign % id)
            else:
                raise AssertionError("bug in always_ff")
            
    def visit_Assign(self, node):
        self.context = OUTPUT
        for n in node.targets:
            self.visit(n)
        self.context = INPUT
        self.visit(node.value)

    def visit_Attribute(self, node):
        self.visit(node.value)

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

         



 
