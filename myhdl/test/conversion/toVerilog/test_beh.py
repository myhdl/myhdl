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

def behRef(count, enable, clock, reset, n):

    @instance
    def logic():
        while 1:
            if reset == ACTIVE_LOW:
                yield reset.posedge
            for i in range(20):
                yield clock.posedge
                if enable:
                    count.next = i
            j = 1
            while j < 25:
                if enable:
                    yield clock.posedge
                yield clock.posedge
                count.next = 2 * j
                j += 1

    return logic

objfile = "beh_inst.o"
analyze_cmd = "iverilog -o %s beh_inst.v tb_beh_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
def beh_v(name, count, enable, clock, reset):
    return setupCosimulation(**locals())

class TestBeh(TestCase):

    def clockGen(self, clock):
        while 1:
            yield delay(10)
            clock.next = not clock
    
    def stimulus(self, enable, clock, reset):
        reset.next = INACTIVE_HIGH
        yield clock.negedge
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = 1
            yield clock.negedge
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield clock.negedge
        raise StopSimulation

    def check(self, count, count_v, enable, clock, reset, n):
        yield reset.posedge
        self.assertEqual(count, count_v)
        while 1:
            yield clock.posedge
            yield delay(1)
            # print "%d count %s count_v %s" % (now(), count, count_v)
            self.assertEqual(count, count_v)
                
    def bench(self, beh):

        m = 8
        n = 2 ** m
 
        count = Signal(intbv(0)[m:])
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]

        beh_inst = toVerilog(beh, count, enable, clock, reset, n=n)
        # beh_inst = beh(count, enable, clock, reset, n=n)
        beh_inst_v = beh_v(beh.__name__, count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(beh_inst, beh_inst_v, clk_1, st_1, ch_1)
        # sim = Simulation(beh_inst,  clk_1, st_1, ch_1)
        return sim

    def testBehRef(self):
        sim = self.bench(behRef)
        sim.run(quiet=1)
        
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

