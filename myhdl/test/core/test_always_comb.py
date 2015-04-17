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

""" Run the unit tests for always_comb """
from __future__ import absolute_import


import random
from random import randrange
# random.seed(3) # random, but deterministic

import unittest
from unittest import TestCase
import inspect

from myhdl import Signal, Simulation, instances, AlwaysCombError, \
                  intbv, delay, StopSimulation, now

from myhdl._always_comb import always_comb, _AlwaysComb, _error

from myhdl._Waiter import _Waiter,_SignalWaiter,_SignalTupleWaiter


QUIET=1

def g():
    pass

x = Signal(0)

class AlwaysCombCompilationTest(TestCase):
    

    def testArgIsFunction(self):
        h = 5
        try:
            always_comb(h)
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()
    
    def testArgIsNormalFunction(self):
        def h():
            yield None
        try:
            always_comb(h)
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()

    def testArgHasNoArgs(self):
        def h(n):
            return n
        try:
            always_comb(h)
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.NrOfArgs)
        else:
            self.fail()

##     def testScope(self):
##         try:
##             always_comb(g)
##         except AlwaysCombError, e:
##             self.assertEqual(e.kind, _error.Scope)
##         else:
##             self.fail()

    def testInfer1(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            c.next = a
            v = u
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a'])
        self.assertEqual(i.inputs, expected)
        
    def testInfer2(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            c.next = x
            g = a
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a', 'x'])
        self.assertEqual(i.inputs, expected)

    def testInfer3(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            c.next = a + x + u
            a = 1
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['x'])
        self.assertEqual(i.inputs, expected)

    def testInfer4(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            c.next = a + x + u
            x = 1
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a'])
        self.assertEqual(i.inputs, expected)
        
        
    def testInfer5(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def h():
            c.next += 1
            a += 1
        try:
            g = always_comb(h).gen
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.SignalAsInout % "c")
        else:
            self.fail()

    def testInfer6(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def h():
            c.next = a
            x.next = c
        try:
            g = always_comb(h).gen
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.SignalAsInout % "c")
        else:
            self.fail()

    def testInfer7(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def h():
            c.next[a:0] = x[b:0]
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a', 'b', 'x'])
        self.assertEqual(i.inputs, expected)
        
    def testInfer8(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            v = 2
            c.next[8:1+a+v] = x[4:b*3+u]
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a', 'b', 'x'])
        self.assertEqual(i.inputs, expected)
         
    def testInfer9(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def h():
            c.next[a-1] = x[b-1]
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a', 'b', 'x'])
        self.assertEqual(i.inputs, expected)
        
    def testInfer10(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def f(x, y, z):
            return 0
        def h():
            c.next = f(a, 2*b, d*x)
        g = always_comb(h).gen
        i = g.gi_frame.f_locals['self']
        expected = set(['a', 'b', 'd', 'x'])
        self.assertEqual(i.inputs, expected)

    def testEmbeddedFunction(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        u = 1
        def h():
            def g():
                e = b
                return e
            c.next = x
            g = a
        try:
            g = always_comb(h)
        except AlwaysCombError as e:
            self.assertEqual(e.kind, _error.EmbeddedFunction)
        else:
            self.fail()


class AlwaysCombSimulationTest1(TestCase):

    def bench(self, function):

        clk = Signal(0)
        a = Signal(0)
        b = Signal(0)
        c = Signal(0)
        d = Signal(0)
        z = Signal(0)
        vectors = [intbv(j) for i in range(32) for j in range(16)]
        random.shuffle(vectors)

        
        def combFunc():
            if __debug__:
                f = x
            x.next = function(a, b, c, d)

        comb = always_comb(combFunc)

        def clkGen():
            while 1:
                yield delay(10)
                clk.next ^= 1

        def logic():
            while 1:
                z.next = function(a, b, c, d)
                yield a, b, c, d

        def stimulus():
            for v in vectors:
                a.next = v[0]
                b.next = v[1]
                c.next = v[2]
                d.next = v[3]
                yield clk.posedge
                yield clk.negedge
                self.assertEqual(x, z)
            raise StopSimulation("always_comb simulation test")

        return instances()
        

    def testAnd(self):
        def andFunction(a, b, c, d):
            return a & b & c & d
        Simulation(self.bench(andFunction)).run(quiet=QUIET)
        
    def testOr(self):
        def orFunction(a, b, c, d):
            return a | b | c | d
        Simulation(self.bench(orFunction)).run(quiet=QUIET)
        
    def testXor(self):
        def xorFunction(a, b, c, d):
            return a ^ b ^ c ^ d
        Simulation(self.bench(xorFunction)).run(quiet=QUIET)

    def testMux(self):
        def muxFunction(a, b, c, d):
            if c:
                return a
            else:
                return b
        Simulation(self.bench(muxFunction)).run(quiet=QUIET)

    def testLogic(self):
        def function(a, b, c, d):
            return not (a & (not b)) | ((not c) & d)
        Simulation(self.bench(function)).run(quiet=QUIET)

        
class AlwaysCombSimulationTest2(TestCase):

    def bench(self, funcName="and"):

        clk = Signal(0)
        a = Signal(0)
        b = Signal(0)
        c = Signal(0)
        d = Signal(0)
        k = Signal(0)
        z = Signal(0)
        x = Signal(0)
        vectors = [intbv(j) for i in range(32) for j in range(16)]
        random.shuffle(vectors)

        def andFunc():
            x.next = a & b & c & d
        def andGenFunc():
            while 1:
                z.next =  a & b & c & d
                yield a, b, c, d
            
        def orFunc():
            x.next = a | b | c | d
        def orGenFunc():
            while 1:
                z.next = a | b | c | d
                yield a, b, c, d
            
        def logicFunc():
            x.next = not (a & (not b)) | ((not c) & d)
        def logicGenFunc():
            while 1:
                z.next = not (a & (not b)) | ((not c) & d)
                yield a, b, c, d

        def incFunc():
            x.next = k + 1
        def incGenFunc():
            while 1:
                z.next = k + 1
                yield k
       
        combFunc = eval(funcName + "Func")
        comb = always_comb(combFunc)
        genFunc = eval(funcName + "GenFunc")
        gen = genFunc()

        def clkGen():
            while 1:
                yield delay(10)
                clk.next ^= 1

        def stimulus():
            for v in vectors:
                a.next = v[0]
                b.next = v[1]
                c.next = v[2]
                d.next = v[3]
                k.next = v
                yield clk.posedge
                yield clk.negedge
                self.assertEqual(x, z)
            raise StopSimulation("always_comb simulation test")

        return comb, gen, clkGen(), stimulus()
        

    def testAnd(self):
        Simulation(self.bench("and")).run(quiet=QUIET)
        
    def testOr(self):
        Simulation(self.bench("or")).run(quiet=QUIET)
        
    def testLogic(self):
        Simulation(self.bench("logic")).run(quiet=QUIET)
        
    def testInc(self):
        Simulation(self.bench("inc")).run(quiet=QUIET)




def SignalGen1(a, b, c, d, r):
    
    @always_comb
    def logic():
        r.next = a

    return logic


def SignalTupleGen1(a, b, c, d, r):

    @always_comb
    def logic():
        r.next = a + b + c

    return logic


        
class InferWaiterTest(TestCase):

    def bench(self, MyHDLFunc, waiterType):

        a, b, c, d, r, s = [Signal(intbv(0)) for i in range(6)]

        inst_r = MyHDLFunc(a, b, c, d, r)
        self.assertEqual(type(inst_r.waiter), waiterType)
        
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
                self.assertEqual(r, s)

        return inst_r, _Waiter(inst_s.gen), _Waiter(stimulus()), _Waiter(check())

    def testSignal1(self):
        sim = Simulation(self.bench(SignalGen1, _SignalWaiter))
        sim.run()
        
    def testSignalTuple1(self):
        sim = Simulation(self.bench(SignalTupleGen1, _SignalTupleWaiter))
        sim.run()



if __name__ == "__main__":
    unittest.main()
