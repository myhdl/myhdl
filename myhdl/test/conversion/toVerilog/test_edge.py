from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *

from util import setupCosimulation

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def edge1(flag, sig, clock):

    sig_Z1 = Signal(bool(0))

    @always(clock.posedge)
    def detect():
        sig_Z1.next = sig
        flag.next = False
        if sig and not sig_Z1:
            flag.next = True

    return detect

def edge2(flag, sig, clock):

    sig_Z1 = Signal(bool(0))

    @always(clock.posedge)
    def detect():
        sig_Z1.next = sig
        flag.next = sig and not sig_Z1

    return detect


def edge3(flag, sig, clock):

    @instance
    def detect():
        sig_Z1 = False
        while True:
            yield clock.posedge
            flag.next = sig and not sig_Z1
            sig_Z1 = sig.val

    return detect


def edge4(flag, sig, clock):

    @instance
    def detect():
        sig_Z1 = False
        while True:
            yield clock.posedge
            flag.next = sig and not sig_Z1
            sig_Z1 = bool(sig)

    return detect

    
def edge_v(name, flag, sig, clock):
    return setupCosimulation(**locals())

class TestEdge(TestCase):
            
    def bench(self, edge):

        clock = Signal(bool(0))
        sig = Signal(bool(0))
        flag = Signal(bool(0))

        sig_Z1 = Signal(bool(0))
        sig_Z2 = Signal(bool(0))

        @always(delay(10))
        def clockgen():
            clock.next = not clock

        @instance
        def stimulus():
            yield clock.negedge
            for i in range(100):
                sig.next = randrange(2)
                yield clock.negedge
            raise StopSimulation

        @always(clock.posedge)
        def delayline():
            sig_Z1.next = sig
            sig_Z2.next = sig_Z1

        @always(clock.negedge)
        def check():
            expected = sig_Z1 and not sig_Z2
            self.assertEqual(flag, expected)

        edge_inst = toVerilog(edge, flag, sig, clock)
        edge_inst_v = edge_v(edge.__name__, flag, sig, clock)

        return clockgen, stimulus, delayline, check, edge_inst_v
          

    def testEdge1(self):
        sim = Simulation(self.bench(edge1))
        sim.run(quiet=1)
        
    def testEdge2(self):
        sim = Simulation(self.bench(edge2))
        sim.run(quiet=1)
        
    def testEdge3(self):
        sim = Simulation(self.bench(edge3))
        sim.run(quiet=1)
        
    def testEdge4(self):
        sim = Simulation(self.bench(edge4))
        sim.run(quiet=1)
        
        

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

