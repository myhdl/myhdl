from __future__ import generators

import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import Simulation, StopSimulation, Signal, \
                  delay, intbv, negedge, posedge, now

from dff import dff
from dff_clkout import dff_clkout

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

class TestDff(TestCase):
    
    vals = [randrange(2) for i in range(1000)]

    def clkGen(self, clk):
        while 1:
            yield delay(10)
            clk.next = not clk
            
    
    def stimulus(self, d, clk, reset):
        reset.next = ACTIVE_LOW
        yield negedge(clk)
        reset.next = INACTIVE_HIGH
        for v in self.vals:
            d.next = v
            yield negedge(clk)
        raise StopSimulation
    
    
    def check(self, q, clk, reset):
        yield posedge(reset)
        v_Z = 0
        first = 1
        for v in self.vals:
            yield posedge(clk)
            if not first:
                self.assertEqual(q, v_Z)
            first = 0
            yield delay(3)
            self.assertEqual(q, v)
            v_Z = v
            

    def bench(self):
        
        q, d, clk, reset = [Signal(intbv(0)) for i in range(4)]
        
        DFF_1 = dff(q, d, clk, reset)
        CLK_1 = self.clkGen(clk)
        ST_1 = self.stimulus(d, clk, reset)
        CH_1 = self.check(q, clk, reset)
        
        sim = Simulation(DFF_1, CLK_1, ST_1, CH_1)
        return sim
    

    def test1(self):
        """ dff test """
        sim = self.bench()
        sim.run(quiet=1)
        
        
    def test2(self):
        """ dff test with simulation suspends """
        sim = self.bench()
        while sim.run(duration=randrange(1,5), quiet=1):
            pass
        

    def bench_clkout(self):
        
        clkout = Signal(intbv(0))
        q = Signal(intbv(0), delay=1)
        d = Signal(intbv(0))
        clk = Signal(intbv(0))
        
        reset = Signal(intbv(0))
        DFF_1 = dff_clkout(clkout, q, d, clk, reset)
        CLK_1 = self.clkGen(clk)
        ST_1 = self.stimulus(d, clkout, reset)
        CH_1 = self.check(q, clkout, reset)
        
        sim = Simulation(DFF_1, CLK_1, ST_1, CH_1)
        return sim

    
    def test1_clkout(self):
        """ dff_clkout test """
        sim = self.bench_clkout()
        sim.run(quiet=1)
        

    def test2_clkout(self):
        """ dff_clkout test with simulation suspends """
        sim = self.bench_clkout()
        while sim.run(duration=randrange(1,5), quiet=1):
            pass
    

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

