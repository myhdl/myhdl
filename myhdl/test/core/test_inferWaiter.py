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

""" Run the unit tests for inferWaiter """
from __future__ import absolute_import

import random
from random import randrange
random.seed(1) # random, but deterministic
from types import GeneratorType

import unittest
from unittest import TestCase

from myhdl import *
from myhdl._Waiter import _inferWaiter, _Waiter
from myhdl._Waiter import _SignalWaiter,_SignalTupleWaiter, _DelayWaiter, \
                          _EdgeWaiter, _EdgeTupleWaiter


QUIET=1

def SignalFunc1(a, b, c, d, r):
    @instance
    def logic():
        while 1:
            yield a
            r.next = a + b + c
    return logic


def SignalFunc2(a, b, c, d, r):
    def logic(a, r):
        while 1:
            yield a
            r.next = a - b + c
    return logic(a, r)

def SignalTupleFunc1(a, b, c, d, r):
    @instance
    def logic():
        while 1:
            yield a, b, c
            r.next = a + b + c
    return logic

def SignalTupleFunc2(a, b, c, d, r):
    def logic(a, r):
        while 1:
            yield a, b, c
            r.next = a - b + c
    return logic(a, r)

def DelayFunc(a, b, c, d, r):
    @instance
    def logic():
        while 1:
            yield delay(3)
            r.next = a + b + c
    return logic

def EdgeFunc1(a, b, c, d, r):
    @instance
    def logic():
        while 1:
            yield c.posedge
            r.next = a + b + c
    return logic

def EdgeFunc2(a, b, c, d, r):
    def logic(c, r):
        while 1:
            yield c.negedge
            r.next = a + b + c
            if a > 5:
                yield c.posedge
                r.next = a - b -c
            else:
                r.next = a + b - c
    return logic(c, r)

def EdgeTupleFunc1(a, b, c, d, r):
    @instance
    def logic():
        while 1:
            yield c.posedge, d.negedge
            r.next = a + b + c
    return logic

def EdgeTupleFunc2(a, b, c, d, r):
    def logic(c, r):
        while 1:
            yield c.negedge, d.posedge
            r.next = a + b + c
            if a > 5:
                yield c.posedge, d.negedge
                r.next = a - b -c
            else:
                r.next = a + b - c
    return logic(c, r)
     
def GeneralFunc(a, b, c, d, r):
    def logic(c, r):
        while 1:
            yield c.negedge, d.posedge
            r.next = a + b + c
            if a > 5:
                yield c, d.negedge
                r.next = a - b -c
            else:
                r.next = a + b - c
    return logic(c, r)
     


class InferWaiterTest(TestCase):

    def bench(self, genFunc, waiterType):

        a, b, c, d, r, s = [Signal(intbv(0)) for i in range(6)]

        gen_inst_r = genFunc(a, b, c, d, r)
        if not isinstance(gen_inst_r, GeneratorType): # decorator type
            gen_inst_r = gen_inst_r.gen
        self.assertEqual(type(_inferWaiter(gen_inst_r)), waiterType)
        
        gen_inst_s = genFunc(a, b, c, d, s)
        if not isinstance(gen_inst_s, GeneratorType): # decorator type
            gen_inst_s = gen_inst_s.gen

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
                self.assertEqual(r, s)

        return gen_inst_r, _Waiter(gen_inst_s), _Waiter(stimulus()), _Waiter(check())

    def testSignal1(self):
        sim = Simulation(self.bench(SignalFunc1, _SignalWaiter))
        sim.run()
        
    def testSignal2(self):
        sim = Simulation(self.bench(SignalFunc2, _SignalWaiter))
        sim.run()
        
    def testSignalTuple1(self):
        sim = Simulation(self.bench(SignalTupleFunc1, _SignalTupleWaiter))
        sim.run()

    def testSignalTuple2(self):
        sim = Simulation(self.bench(SignalTupleFunc2, _SignalTupleWaiter))
        sim.run()

    def testDelay(self):
        sim = Simulation(self.bench(DelayFunc, _DelayWaiter))
        sim.run()

    def testEdge1(self):
        sim = Simulation(self.bench(EdgeFunc1, _EdgeWaiter))
        sim.run()
        
    def testEdge2(self):
        sim = Simulation(self.bench(EdgeFunc2, _EdgeWaiter))
        sim.run()

    def testEdgeTuple1(self):
        sim = Simulation(self.bench(EdgeTupleFunc1, _EdgeTupleWaiter))
        sim.run()

    def testEdgeTuple2(self):
        sim = Simulation(self.bench(EdgeTupleFunc2, _EdgeTupleWaiter))
        sim.run()

    def testGeneral(self):
        sim = Simulation(self.bench(GeneralFunc, _Waiter))
        sim.run()


if __name__ == "__main__":
    unittest.main()
