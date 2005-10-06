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

""" Run the unit tests for inferWaiter """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import random
from random import randrange
random.seed(1) # random, but deterministic

import unittest
from unittest import TestCase

from myhdl import *
from myhdl._Waiter import _inferWaiter, _Waiter
from myhdl._Waiter import _SignalWaiter,_SignalTupleWaiter, _DelayWaiter, \
                          _EdgeWaiter, _EdgeTupleWaiter


QUIET=1

def SignalGen1(a, b, c, d, r):
    while 1:
        yield a
        r.next = a + b + c

def SignalGen2(a, b, c, d, r):
    def logic(a, r):
        while 1:
            yield a
            r.next = a - b + c
    return logic(a, r)

def SignalTupleGen1(a, b, c, d, r):
    while 1:
        yield a, b, c
        r.next = a + b + c

def SignalTupleGen2(a, b, c, d, r):
    def logic(a, r):
        while 1:
            yield a, b, c
            r.next = a - b + c
    return logic(a, r)

def DelayGen(a, b, c, d, r):
    while 1:
        yield delay(3)
        r.next = a + b + c

def EdgeGen1(a, b, c, d, r):
    while 1:
        yield posedge(c)
        r.next = a + b + c

def EdgeGen2(a, b, c, d, r):
    def logic(c, r):
        while 1:
            yield negedge(c)
            r.next = a + b + c
            if a > 5:
                yield posedge(c)
                r.next = a - b -c
            else:
                r.next = a + b - c
    return logic(c, r)

def EdgeTupleGen1(a, b, c, d, r):
    while 1:
        yield posedge(c), negedge(d)
        r.next = a + b + c

def EdgeTupleGen2(a, b, c, d, r):
    def logic(c, r):
        while 1:
            yield negedge(c), posedge(d)
            r.next = a + b + c
            if a > 5:
                yield posedge(c), negedge(d)
                r.next = a - b -c
            else:
                r.next = a + b - c
    return logic(c, r)
     


class InferWaiterTest(TestCase):

    def bench(self, genFunc, waiterType):

        a, b, c, d, r, s = [Signal(intbv(0)) for i in range(6)]

        gen_inst_r = genFunc(a, b, c, d, r)
        self.assertEqual(type(_inferWaiter(gen_inst_r)), waiterType)
        
        gen_inst_s = genFunc(a, b, c, d, s)

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
        sim = Simulation(self.bench(SignalGen1, _SignalWaiter))
        sim.run()
        
    def testSignal2(self):
        sim = Simulation(self.bench(SignalGen2, _SignalWaiter))
        sim.run()
        
    def testSignalTuple1(self):
        sim = Simulation(self.bench(SignalTupleGen1, _SignalTupleWaiter))
        sim.run()

    def testSignalTuple2(self):
        sim = Simulation(self.bench(SignalTupleGen2, _SignalTupleWaiter))
        sim.run()

    def testDelay(self):
        sim = Simulation(self.bench(DelayGen, _DelayWaiter))
        sim.run()

    def testEdge1(self):
        sim = Simulation(self.bench(EdgeGen1, _EdgeWaiter))
        sim.run()
        
    def testEdge2(self):
        sim = Simulation(self.bench(EdgeGen2, _EdgeWaiter))
        sim.run()

    def testEdgeTuple1(self):
        sim = Simulation(self.bench(EdgeTupleGen1, _EdgeTupleWaiter))
        sim.run()

    def testEdgeTuple2(self):
        sim = Simulation(self.bench(EdgeTupleGen2, _EdgeTupleWaiter))
        sim.run()


if __name__ == "__main__":
    unittest.main()
