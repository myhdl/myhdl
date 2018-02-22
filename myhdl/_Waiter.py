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

""" Module that provides the _Waiter class """
from __future__ import absolute_import


from types import GeneratorType

import ast
import inspect


from myhdl._util import _dedent
from myhdl._delay import delay
from myhdl._join import join
from myhdl._Signal import _Signal, _WaiterList, posedge, negedge
from myhdl import _simulator
from myhdl._simulator import _futureEvents


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
            clause = next(self.generator)
        except StopIteration:
            if self.caller:
                waiters.append(self.caller)
            raise  # again

        if isinstance(clause, _WaiterList):
            clauses = (clause,)
        elif isinstance(clause, (tuple, list)):
            clone.nrTriggers = len(clause)
            if clause:
                clauses = clause
            else:
                clauses = (None,)
        elif isinstance(clause, join):
            clone.semaphore = len(clause._args) - 1
            clauses = clause._args
        else:
            clauses = (clause,)

        nr = len(clauses)
        for clause in clauses:
            if isinstance(clause, _WaiterList):
                clause.append(clone)
                if nr > 1:
                    actives[id(clause)] = clause
            elif isinstance(clause, _Signal):
                wl = clause._eventWaiters
                wl.append(clone)
                if nr > 1:
                    actives[id(wl)] = wl
            elif isinstance(clause, delay):
                t = _simulator._time
                schedule((t + clause._time, clone))
            elif isinstance(clause, GeneratorType):
                waiters.append(_Waiter(clause, clone))
            elif isinstance(clause, _Instantiator):
                waiters.append(_Waiter(clause.gen, clone))
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
        clause = next(self.generator)
        schedule((_simulator._time + clause._time, self))


class _EdgeWaiter(_Waiter):

    __slots__ = ('generator', 'hasRun')

    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0

    def next(self, waiters, actives, exc):
        clause = next(self.generator)
        clause.append(self)


class _EdgeTupleWaiter(_Waiter):

    __slots__ = ('generator', 'hasRun')

    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0

    def next(self, waiters, actives, exc):
        if self.hasRun:
            raise StopIteration
        clauses = next(self.generator)
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
        clause = next(self.generator)
        clause._eventWaiters.append(self)


class _SignalTupleWaiter(_Waiter):

    __slots__ = ('generator', 'hasRun')

    def __init__(self, generator):
        self.generator = generator
        self.hasRun = 0

    def next(self, waiters, actives, exc):
        if self.hasRun:
            raise StopIteration
        clauses = next(self.generator)
        self.hasRun = 1
        clone = _SignalTupleWaiter(self.generator)
        for clause in clauses:
            wl = clause._eventWaiters
            wl.append(clone)
            actives[id(wl)] = wl


#_kind = enum("SIGNAL_TUPLE", "EDGE_TUPLE", "SIGNAL", "EDGE", "DELAY", "UNDEFINED")
class _kind(object):
    SIGNAL_TUPLE = 1
    EDGE_TUPLE = 2
    SIGNAL = 3
    EDGE = 4
    DELAY = 5
    UNDEFINED = 6


def _inferWaiter(gen):
    f = gen.gi_frame
    s = inspect.getsource(f)
    s = _dedent(s)
    root = ast.parse(s)
    root.symdict = f.f_globals.copy()
    root.symdict.update(f.f_locals)
    # print ast.dump(root)
    v = _YieldVisitor(root)
    v.visit(root)
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


class _YieldVisitor(ast.NodeVisitor):

    def __init__(self, root):
        self.kind = None
        self.root = root

    def visit_Yield(self, node):
        self.visit(node.value)
        if not hasattr(node.value, 'kind'):
            self.kind = _kind.UNDEFINED
        elif not self.kind:
            self.kind = node.value.kind
        elif self.kind != node.value.kind:
            self.kind = _kind.UNDEFINED

    def visit_Tuple(self, node):
        kind = None
        for elt in node.elts:
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

    def visit_Call(self, node):
        fn = node.func
        if not isinstance(fn, ast.Name):
            node.kind = _kind.UNDEFINED
            return
        self.visit(fn)
        node.kind = fn.kind

    def visit_Name(self, node):
        n = node.id
        node.kind = _kind.UNDEFINED
        if n in self.root.symdict:
            obj = self.root.symdict[n]
            if isinstance(obj, _Signal):
                node.kind = _kind.SIGNAL
            elif obj is delay:
                node.kind = _kind.DELAY
            elif obj is posedge or obj is negedge:
                node.kind = _kind.EDGE

    def visit_Attribute(self, node):
        node.kind = _kind.UNDEFINED
        if node.attr in ('posedge', 'negedge'):
            node.kind = _kind.EDGE


# avoid problems with recursive imports
from myhdl._instance import _Instantiator
