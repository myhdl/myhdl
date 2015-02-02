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

def decRef(count, enable, clock, reset, n):
    """ Decrementer with enable.
    
    count -- output
    enable -- control input, decrement when 1
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
                    if count == -n:
                        count.next = n-1
                    else:
                        count.next = count - 1
    return logic
                
def dec(count, enable, clock, reset, n):
    """ Decrementer with enable.
    
    count -- output
    enable -- control input, decrement when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """
    @instance
    def decProcess():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    if count == -n:
                        count.next = n-1
                    else:
                        count.next = count - 1
    return decProcess


def decFunc(count, enable, clock, reset, n):

    def decFuncFunc(cnt):
        count_next = intbv(0, min=-n, max=n)
        if count == -n:
            count_next[:] = n-1
        else:
            count_next[:] = cnt - 1
        return count_next

    @always(clock.posedge, reset.negedge)
    def decFuncGen():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = decFuncFunc(count)

    return decFuncGen


def decTask(count, enable, clock, reset, n):
    
    def decTaskFunc(cnt, enable, reset, n):
        if enable:
            if cnt == -n:
                cnt.next = n-1
            else:
                cnt.next = cnt - 1

    @instance
    def decTaskGen():
        cnt = intbv(0, min=-n, max=n)
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                cnt[:] = 0
                count.next = 0
            else:
                # print count
                decTaskFunc(cnt, enable, reset, n)
                count.next = cnt

    return decTaskGen


def decTaskFreeVar(count, enable, clock, reset, n):
    
    def decTaskFunc():
        if enable:
            if count == -n:
                count.next = n-1
            else:
                count.next = count - 1

    @instance
    def decTaskGen():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                # print count
                decTaskFunc()

    return decTaskGen


      
def dec_v(name, count, enable, clock, reset):
    return setupCosimulation(**locals())

class TestDec(TestCase):

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
                if expect == -n:
                    expect = n-1
                else:
                    expect -= 1
            yield delay(1)
            # print "%d count %s expect %s count_v %s" % (now(), count, expect, count_v)
            self.assertEqual(count, expect)
            self.assertEqual(count, count_v)
                
    def bench(self, dec):

        m = 8
        n = 2 ** (m-1)
  
        count = Signal(intbv(0, min=-n, max=n))
        count_v = Signal(intbv(0, min=-n, max=n))
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]

        dec_inst_ref = decRef(count, enable, clock, reset, n=n)
        dec_inst = toVerilog(dec, count, enable, clock, reset, n=n)
        # dec_inst = dec(count, enable, clock, reset, n=n)
        dec_inst_v = dec_v(dec.__name__, count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(dec_inst_ref, dec_inst_v, clk_1, st_1, ch_1)
        return sim

    def testDecRef(self):
        sim = self.bench(decRef)
        sim.run(quiet=1)
        
    def testDec(self):
        sim = self.bench(dec)
        sim.run(quiet=1)
        
    def testDecFunc(self):
        sim = self.bench(decFunc)
        sim.run(quiet=1)

## signed inout in task doesn't work yet in Icarus
##     def testDecTask(self):
##         sim = self.bench(decTask)
##         sim.run(quiet=1)
        
    def testDecTaskFreeVar(self):
        sim = self.bench(decTaskFreeVar)
        sim.run(quiet=0)

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

