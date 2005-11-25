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

""" Module that provides the _Waiter class """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from types import GeneratorType

import compiler
from compiler import ast as astNode
import inspect
import re

from myhdl._delay import delay
from myhdl._join import join
from myhdl._Signal import Signal, _WaiterList, posedge, negedge
from myhdl import _simulator
from myhdl._simulator import _siglist, _futureEvents
from myhdl._enum import enum

schedule = _futureEvents.append


class _Waiter(object):

    __slots__ = ('caller', 'generator', 'hasRun', 'nrTriggers', 'semaphore')
    
    def __init__(self, generator, caller=None):
        self.caller = caller
        self.generator = generator
        self.hasRun = 0
        self.nrTriggers = 1
        self.semaphore = 0
        
    def next(self, waiters, actives, exc):

        if self.hasRun:
            raise StopIteration

        if self.semaphore:
            self.semaphore -= 1
            raise StopIteration
        
        if self.nrTriggers == 1:
            clone = self
        else:
            self.hasRun = 1
            clone = _Waiter(self.generator, self.caller)
            
        try:
            clause = self.generator.next()
        except StopIteration:
            if self.caller:
                waiters.append(self.caller)
            raise # again
            
        if isinstance(clause, _WaiterList):
            clauses = (clause,)
        elif isinstance(clause, (tuple, list)):
            clone.nrTriggers = len(clause)
            if clause:
                clauses = clause
            else:
                clauses = (None,)
        elif isinstance(clause, join):
            clone.semaphore = len(clause._args)-1
            clauses = clause._args
        else:
            clauses = (clause,)
            
        nr = len(clauses)
        for clause in clauses:
            if isinstance(clause, _WaiterList):
                clause.append(clone)
                if nr > 1:
                    actives[id(clause)] = clause
            elif isinstance(clause, Signal):
                wl = clause._eventWaiters
                wl.append(clone)
                if nr > 1:
                    actives[id(wl)] = wl
            elif isinstance(clause, delay):
                t = _simulator._time
                schedule((t + clause._time, clone))
            elif isinstance(clause, GeneratorType):
                waiters.append(_Waiter(clause, clone))
            elif isinstance(clause, join):
                waiters.append(_Waiter(clause._generator(), clone))
            elif clause is None:
                waiters.append(clone)
            elif isinstance(clause, Exception):
                waiters.append(clone)
                if not exc:
                    exc.append(clause)
            else:
                raise TypeError("yield clause %s has type %s" %
                                (repr(clause), type(clause)))
    
    
class _DelayWaiter(_Waiter):
    
    __slots__ = ('generator')
    
    def __init__(self, generator):
        self.generator = generator
    
    def next(self, waiters, actives, exc):
        clause = self.generator.next()
        schedule((_simulator._time + clause._time, self))
        

class _EdgeWaiter(_Waiter):
    
    __slots__ = ('generator', 'hasRun')
     
    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0
    
    def next(self, waiters, actives, exc):
        clause = self.generator.next()
        clause.append(self)
        
    
class _EdgeTupleWaiter(_Waiter):
    
    __slots__ = ('generator', 'hasRun')
    
    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0

    def next(self, waiters, actives, exc):
        if self.hasRun:
            raise StopIteration
        clauses = self.generator.next()
        self.hasRun = 1
        clone = _EdgeTupleWaiter(self.generator)
        for clause in clauses:
            clause.append(clone)
            actives[id(clause)] = clause
            
            
class _SignalWaiter(_Waiter):
    
    __slots__ = ('generator', 'hasRun')
     
    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0
    
    def next(self, waiters, actives, exc):
        clause = self.generator.next()
        clause._eventWaiters.append(self)
        

class _SignalTupleWaiter(_Waiter):
    
    __slots__ = ('generator', 'hasRun')
    
    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0

    def next(self, waiters, actives, exc):
        if self.hasRun:
            raise StopIteration
        clauses = self.generator.next()
        self.hasRun = 1
        clone = _SignalTupleWaiter(self.generator)
        for clause in clauses:
            wl = clause._eventWaiters
            wl.append(clone)
            actives[id(wl)] = wl
            

_kind = enum("SIGNAL_TUPLE", "EDGE_TUPLE", "SIGNAL", "EDGE", "DELAY", "UNDEFINED")

def _inferWaiter(gen):
    f = gen.gi_frame
    s = inspect.getsource(f)
    # remove decorators
    s = re.sub(r"@.*", "", s)
    s = s.lstrip()
    ast = compiler.parse(s)
    ast.symdict = f.f_globals.copy()
    ast.symdict.update(f.f_locals)
    v = _YieldVisitor(ast)
    compiler.walk(ast, v)
    if v.kind == _kind.EDGE_TUPLE:
        return _EdgeTupleWaiter(gen)
    if v.kind == _kind.SIGNAL_TUPLE:
        return _SignalTupleWaiter(gen)
    if v.kind == _kind.DELAY:
        return _DelayWaiter(gen)
    if v.kind == _kind.EDGE:
        return _EdgeWaiter(gen)
    if v.kind == _kind.SIGNAL:
        return _SignalWaiter(gen)
    # default
    return _Waiter(gen)

class _YieldVisitor(object):

    def __init__(self, ast):
        self.ast = ast
        self.kind = None

    def visitChildNodes(self, node, *args):
        for n in node.getChildNodes():
            self.visit(n, *args)

    def visitYield(self, node, *args):
        self.visit(node.value)
        if not hasattr(node.value, 'kind'):
            self.kind = _kind.UNDEFINED
        elif not self.kind:
            self.kind = node.value.kind
        elif self.kind != node.value.kind:
            self.kind = _kind.UNDEFINED

    def visitTuple(self, node, *args):
        kind = None
        for elt in node.nodes:
            self.visit(elt)
            if not hasattr(elt, 'kind'):
                kind = _kind.UNDEFINED
            elif not kind:
                kind = elt.kind
            elif kind != elt.kind:
                kind = _kind.UNDEFINED
        if kind == _kind.SIGNAL:
            node.kind = _kind.SIGNAL_TUPLE
        elif kind == _kind.EDGE:
            node.kind = _kind.EDGE_TUPLE
        else:
            node.kind = _kind.UNDEFINED

    def visitCallFunc(self, node, *args):
        fn = node.node
        if not isinstance(fn, astNode.Name):
            node.kind = _kind.UNDEFINED
            return
        self.visit(fn)
        node.kind = fn.kind
                
    def visitName(self, node, *args):
        n = node.name
        node.kind = _kind.UNDEFINED
        if n in self.ast.symdict:
            obj = self.ast.symdict[n]
            if isinstance(obj, Signal):
                node.kind = _kind.SIGNAL
            elif obj is delay:
                node.kind = _kind.DELAY
            elif obj in (posedge, negedge):
                node.kind = _kind.EDGE

    def visitGetattr(self, node, *args):
        node.kind = _kind.UNDEFINED
        if node.attrname in ('posedge', 'negedge'):
            node.kind = _kind.EDGE
               
                
        

        

    
