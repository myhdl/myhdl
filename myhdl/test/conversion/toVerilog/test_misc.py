from __future__ import absolute_import
import unittest
import os
path = os.path
from random import randrange

from myhdl import *

from util import setupCosimulation

### test of constant wire support ###

# example from Frank Palazollo
def or_gate(a,b,c):
    @instance
    def logic():
        while 1:
            c.next = a | b
            yield a, b
    return logic
        
def my_bundle(p,q):
        r = Signal(bool(0))
        gen_or = or_gate(p,r,q)
        return instances()

# additional level of hierarchy
def ConstWire2(p, q):
    r = Signal(bool(1))
    s = Signal(bool(1))
    inst1 = my_bundle(p, r)
    inst2 = or_gate(r, s, q)
    return inst1, inst2

def adder(a, b, c):
    @instance
    def logic():
        while 1:
            yield a, b
            c.next = a + b
    return logic

def ConstWire3(p, q):
    t = Signal(intbv(17)[5:])
    adder_inst = adder(p, t, q)
    return instances()

        
def ConstWire_v(name, p, q):
    return setupCosimulation(**locals())

class TestConstWires(unittest.TestCase):

    def benchBool(self, ConstWire):
        
        p = Signal(bool(0))
        q = Signal(bool(0))
        q_v = Signal(bool(0))

        constwire_inst = toVerilog(ConstWire, p, q)
        constwire_v_inst = ConstWire_v(ConstWire.__name__, p, q_v)

        def stimulus():
            for i in range(100):
                p.next = randrange(2)
                yield delay(10)
                self.assertEqual(q, q_v)

        return stimulus(), constwire_inst, constwire_v_inst

    def testConstWire1(self):
        sim = self.benchBool(my_bundle)
        Simulation(sim).run()

    def testConstWire2(self):
        sim = self.benchBool(ConstWire2)
        Simulation(sim).run()        

    def benchIntbv(self, ConstWire):
        
        p = Signal(intbv(0)[8:])
        q = Signal(intbv(0)[8:])
        q_v = Signal(intbv(0)[8:])

        constwire_inst = toVerilog(ConstWire, p, q)
        constwire_v_inst = ConstWire_v(ConstWire.__name__, p, q_v)

        def stimulus():
            for i in range(100):
                p.next = i
                yield delay(10)
                self.assertEqual(q, q_v)
                
        return stimulus(), constwire_inst, constwire_v_inst
        
    def testConstWire3(self):
        sim = self.benchIntbv(ConstWire3)
        Simulation(sim).run()


### tests of code ignore facility during translation ###

def adderRef(a, b, c):
    @instance
    def logic():
        while 1:
            yield a, b
            c.next = a + b
    return logic
        
def adderDebug(a, b, c):
    @instance
    def logic():
        while 1:
            yield a, b
            if __debug__:
                import string
            c.next = a + b
    return logic

        
def Ignorecode_v(name, a, b, c):
    return setupCosimulation(**locals())

class TestIgnoreCode(unittest.TestCase):

    def bench(self, adder):

        a = Signal(intbv(0)[8:])
        b = Signal(intbv(0)[8:])
        c = Signal(intbv(0)[9:])
        c_v = Signal(intbv(0)[9:])

        ignorecode_inst = toVerilog(adder, a, b, c)
        # ignorecode_inst = adder(a, b, c)
        ignorecode_v_inst = Ignorecode_v(adder.__name__, a, b, c_v)

        def stimulus():
            for i in range(100):
                a.next = randrange(2**8)
                b.next = randrange(2**8)
                yield delay(10)
                self.assertEqual(c, c_v)
                
        return stimulus(), ignorecode_inst, ignorecode_v_inst
        
    def testAdderRef(self):
        sim = self.bench(adderRef)
        Simulation(sim).run()
        
    def testAdderDebug(self):
        sim = self.bench(adderDebug)
        Simulation(sim).run()
        

        
if __name__ == '__main__':
    unittest.main()
