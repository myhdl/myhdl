from __future__ import generators

import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def inc(count, enable, clock, reset, n):
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n


analyze_cmd = "iverilog -o inc_1 inc_1.v tb_inc_1.v"
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi inc_1"
      
 
def top(count, enable, clock, reset, n, arch="myhdl"):
    if arch == "verilog":
        if path.exists("inc_1"):
            os.remove("inc_1")
        os.system(analyze_cmd)
        return Cosimulation(simulate_cmd, **locals())
    else:
        inc_inst = inc(count, enable, clock, reset, n)
        return inc_inst

class TestInc(TestCase):

    def clockGen(self, clock):
        while 1:
            yield delay(10)
            clock.next = not clock
    
    def stimulus(self, enable, clock, reset):
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield negedge(clock)
        raise StopSimulation

    def check(self, count, count_v, enable, clock, reset, n):
        expect = 0
        yield posedge(reset)
        self.assertEqual(count, expect)
        self.assertEqual(count, count_v)
        while 1:
            yield posedge(clock)
            if enable:
                expect = (expect + 1) % n
            yield delay(1)
            # print "%d count %s expect %s" % (now(), count, expect)
            self.assertEqual(count, expect)
            self.assertEqual(count, count_v)
                
    def bench(self):

        m = 8
        n = 2 ** m
 
        count = Signal(intbv(0)[m:])
        count_v = Signal(intbv(0)[m:])
        enable, clock, reset = [Signal(bool()) for i in range(3)]

        inc_1 = toVerilog(top, count, enable, clock, reset, n=n)
        inc_v = top(count_v, enable, clock, reset, n=n, arch='verilog')
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(inc_1, inc_v, clk_1, st_1, ch_1)
        return sim

    def test(self):
        """ Check increment operation """
        sim = self.bench()
        sim.run(quiet=1)
        

          
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

