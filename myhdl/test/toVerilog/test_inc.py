import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def incRef(count, enable, clock, reset, n):
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

## def incTaskFunc(count, count_in, enable, clock, reset, n):
##     if enable:
##         count.next = (count_in + 1) % n

## def incTask(count, enable, clock, reset, n):
##     while 1:
##         yield posedge(clock), negedge(reset)
##         if reset == ACTIVE_LOW:
##             count.next = 0
##         else:
##             incTaskFunc(count, count, enable, clock, reset, n)

def incTask(count, enable, clock, reset, n):
    
    def incTaskFunc(cnt, enable, reset, n):
        if enable:
            cnt[:] = (cnt + 1) % n
 
    def incTaskGen():
        cnt = intbv(0)[8:]
        while 1:
            yield posedge(clock), negedge(reset)
            if reset == ACTIVE_LOW:
                cnt[:] = 0
                count.next = 0
            else:
                # print count
                incTaskFunc(cnt, enable, reset, n)
                count.next = cnt

    return incTaskGen()


def incTaskFreeVar(count, enable, clock, reset, n):
    
    def incTaskFunc():
        if enable:
            count.next = (count + 1) % n
 
    def incTaskGen():
        while 1:
            yield posedge(clock), negedge(reset)
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                # print count
                incTaskFunc()

    return incTaskGen()
        
def incGen(count, enable, clock, reset, n):

    def gen():
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

    def inc():
        while 1:
            yield gen()

    return inc()

objfile = "inc_inst.o"
analyze_cmd = "iverilog -o %s inc_inst.v tb_inc_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
def inc_v(count, enable, clock, reset):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestInc(TestCase):

    def clockGen(self, clock):
        while 1:
            yield delay(10)
            clock.next = not clock
    
    def stimulus(self, enable, clock, reset):
        reset.next = INACTIVE_HIGH
        yield negedge(clock)
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = 1
            yield negedge(clock)
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
            # print "%d count %s expect %s count_v %s" % (now(), count, expect, count_v)
            self.assertEqual(count, expect)
            self.assertEqual(count, count_v)
                
    def bench(self, inc):

        m = 8
        n = 2 ** m
 
        count = Signal(intbv(0)[m:])
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]

        inc_inst_ref = incRef(count, enable, clock, reset, n=n)
        inc_inst = toVerilog(inc, count, enable, clock, reset, n=n)
        # inc_inst = inc(count, enable, clock, reset, n=n)
        inc_inst_v = inc_v(count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(inc_inst_ref, inc_inst_v, clk_1, st_1, ch_1)
        return sim

    def testIncRef(self):
        """ Check increment operation """
        sim = self.bench(incRef)
        sim.run(quiet=1)
        
    def testIncTask(self):
        sim = self.bench(incTask)
        sim.run(quiet=1)
        
    def testIncTaskFreeVar(self):
        sim = self.bench(incTaskFreeVar)
        sim.run(quiet=1)
        
##     def testIncGen(self):
##         sim = self.bench(incGen)
##         sim.run(quiet=1)
        

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

