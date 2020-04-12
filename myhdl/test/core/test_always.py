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
#  License along with this librardy; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Run the unit tests for the @always decorator """
from random import randrange

from myhdl import (AlwaysError, Signal, Simulation, StopSimulation, delay,
                   instances, intbv, now)
from myhdl._always import _error, always
from myhdl._Waiter import (_DelayWaiter, _EdgeTupleWaiter, _EdgeWaiter,
                           _SignalTupleWaiter, _SignalWaiter, _Waiter)
from helpers import raises_kind

# random.seed(3) # random, but deterministic


QUIET=1


def g():
    pass

x = Signal(0)


class TestAlwaysCompilation:

    def testArgIsFunction(self):
        h = 5
        with raises_kind(AlwaysError, _error.ArgType):
            always(delay(3))(h)

    def testArgIsNormalFunction(self):
        with raises_kind(AlwaysError, _error.ArgType):
            @always(delay(3))
            def h():
                yield None

    def testArgHasNoArgs(self):
        with raises_kind(AlwaysError, _error.NrOfArgs):
            @always(delay(3))
            def h(n):
                return n

    def testDecArgType1(self):
        with raises_kind(AlwaysError, _error.DecArgType):
            @always
            def h(n):
                return n

    def testDecArgType2(self):
        with raises_kind(AlwaysError, _error.DecArgType):
            @always(g)
            def h(n):
                return n


def SignalFunc1(a, b, c, d, r):

    @always(a)
    def logic():
        r.next = a + b + c + d

    return logic


def SignalTupleFunc1(a, b, c, d, r):

    @always(a, b, c)
    def logic():
        r.next = a + b + c + d

    return logic


def DelayFunc(a, b, c, d, r):

    @always(delay(3))
    def logic():
        r.next = a + b + c + d

    return logic


def EdgeFunc1(a, b, c, d, r):

    @always(c.posedge)
    def logic():
        r.next = a + b + c + d

    return logic


def EdgeTupleFunc1(a, b, c, d, r):

    @always(c.posedge, d.negedge)
    def logic():
        r.next = a + b + c + d

    return logic


def GeneralFunc(a, b, c, d, r):

    @always(c.posedge, d)
    def logic():
        r.next = a + b + c + d

    return logic


class TestInferWaiter:

    def bench(self, MyHDLFunc, waiterType):

        a, b, c, d, r, s = [Signal(intbv(0)) for i in range(6)]

        inst_r = MyHDLFunc(a, b, c, d, r)
        assert type(inst_r.waiter) == waiterType

        inst_s = MyHDLFunc(a, b, c, d, s)

        def stimulus():
            for i in range(1000):
                yield delay(randrange(1, 10))
                if randrange(2):
                    a.next = randrange(32)
                if randrange(2):
                       b.next = randrange(32)
                c.next = randrange(2)
                d.next = randrange(2)
            raise StopSimulation

        def check():
            while 1:
                yield a, b, c, r, s
                assert r == s

        return inst_r, _Waiter(inst_s.gen), _Waiter(stimulus()), _Waiter(check())

    def testSignal1(self):
        sim = Simulation(self.bench(SignalFunc1, _SignalWaiter))
        sim.run()

    def testSignalTuple1(self):
        sim = Simulation(self.bench(SignalTupleFunc1, _SignalTupleWaiter))
        sim.run()

    def testDelay(self):
        sim = Simulation(self.bench(DelayFunc, _DelayWaiter))
        sim.run()

    def testEdge1(self):
        sim = Simulation(self.bench(EdgeFunc1, _EdgeWaiter))
        sim.run()

    def testEdgeTuple1(self):
        sim = Simulation(self.bench(EdgeTupleFunc1, _EdgeTupleWaiter))
        sim.run()

    def testGeneral(self):
        sim = Simulation(self.bench(GeneralFunc, _Waiter))
        sim.run()
