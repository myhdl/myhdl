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

from __future__ import generators

import inspect
from types import FunctionType
import compiler

from myhdl import Signal
from myhdl._util import _isgeneratorfunction

class Error(Exception):
    """always_comb Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class ArgumentError(Error):
    """ always_comb argument should be a normal (non-generator) function"""
    
class NrOfArgsError(Error):
    """ always_comb argument should be a function without arguments"""

class ScopeError(Error):
    """always_comb argument should be a local function"""
    
class SignalAsInoutError(Error):
    """signal used as inout in always_comb function argument"""
    

def always_comb(func):
    f = inspect.getouterframes(inspect.currentframe())[1][0]
    if type(func) is not FunctionType:
        raise ArgumentError
    if _isgeneratorfunction(func):
        raise ArgumentError
    if func.func_code.co_argcount:
        raise NrOfArgsError
    if func.func_name not in f.f_locals:
        raise ScopeError
    varnames = func.func_code.co_varnames
    sigdict = {}
    for dict in (f.f_locals, f.f_globals):
        for n, v in dict.items():
            if isinstance(v, Signal) and n not in varnames:
                sigdict[n] = v
    c = _AlwaysComb(func, sigdict)
    return c.genfunc()
   

INPUT, OUTPUT, INOUT = range(3)

class _SigNameVisitor(object):
    def __init__(self, sigdict):
        self.inputs = []
        self.outputs = []
        self.sigdict = sigdict

    def visitModule(self, node):
        inputs = self.inputs
        outputs = self.outputs
        self.visit(node.node)
        for n in inputs:
            if n in outputs:
                raise SignalAsInoutError(n)

    def visitName(self, node, access=INPUT):
        if node.name not in self.sigdict:
            return
        if access == INPUT:
            self.inputs.append(node.name)
        elif access == OUTPUT:
            self.outputs.append(node.name)
        elif access == INOUT:
            raise SignalAsInoutError(node.name)
        else:
            raise Error
            
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
        

class _AlwaysComb(object):

    def __init__(self, func, sigdict):
        self.func = func
        self.sigdict = sigdict
        s = inspect.getsource(func)
        s = s.lstrip()
        tree = compiler.parse(s)
        v = _SigNameVisitor(sigdict)
        compiler.walk(tree, v)
        v.inputs.sort()
        v.outputs.sort()
        self.inputs = v.inputs
        self.outputs = v.outputs

    def genfunc(self):
        inputsigs = tuple([self.sigdict[n] for n in self.inputs])
        func = self.func
        while 1:
            func()
            yield inputsigs
 
