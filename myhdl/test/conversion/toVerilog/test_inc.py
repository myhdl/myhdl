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

def incRef(count, enable, clock, reset, n):
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """
    @instance
    def logic():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return logic
                
def inc(count, enable, clock, reset, n):
    
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    
    """
    
    @always(clock.posedge, reset.negedge)
    def incProcess():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n
                
    return incProcess

def inc2(count, enable, clock, reset, n):
    
    @always(clock.posedge, reset.negedge)
    def incProcess():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                if count == n-1:
                    count.next = 0
                else:
                    count.next = count + 1
    return incProcess
    

def incTask(count, enable, clock, reset, n):
    
    def incTaskFunc(cnt, enable, reset, n):
        if enable:
            cnt[:] = (cnt + 1) % n

    @instance
    def incTaskGen():
        cnt = intbv(0)[8:]
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                cnt[:] = 0
                count.next = 0
            else:
                # print count
                incTaskFunc(cnt, enable, reset, n)
                count.next = cnt

    return incTaskGen


def incTaskFreeVar(count, enable, clock, reset, n):
    
    def incTaskFunc():
        if enable:
            count.next = (count + 1) % n

    @always(clock.posedge, reset.negedge)
    def incTaskGen():
        if reset == ACTIVE_LOW:
           count.next = 0
        else:
            # print count
            incTaskFunc()

    return incTaskGen

      
def inc_v(name, count, enable, clock, reset):
    return setupCosimulation(**locals())

class TestInc(TestCase):

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
        expect = 0
        yield reset.posedge
        self.assertEqual(count, expect)
        self.assertEqual(count, count_v)
        while 1:
            yield clock.posedge
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
        inc_inst_v = inc_v(inc.__name__, count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(inc_inst_ref, inc_inst_v, clk_1, st_1, ch_1)
        return sim

    def testIncRef(self):
        """ Check increment operation """
        sim = self.bench(incRef)
        sim.run(quiet=1)
        
    def testInc(self):
        """ Check increment operation """
        sim = self.bench(inc)
        sim.run(quiet=1)
        
    def testInc2(self):
        """ Check increment operation """
        sim = self.bench(inc2)
        sim.run(quiet=1)
        
    def testIncTask(self):
        sim = self.bench(incTask)
        sim.run(quiet=1)
        
    def testIncTaskFreeVar(self):
        sim = self.bench(incTaskFreeVar)
        sim.run(quiet=1)

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

