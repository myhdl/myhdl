import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl._toVerilog import ToVerilogError, _error

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

## def incTask(count, enable, clock, reset, n):
    
##     def incTaskFunc(cnt, enable, reset, n):
##         if enable:
##             cnt[:] = (cnt + 1) % n
 
##     def incTaskGen():
##         cnt = intbv(0)[8:]
##         while 1:
##             yield posedge(clock), negedge(reset)
##             if reset == ACTIVE_LOW:
##                 cnt[:] = 0
##                 count.next = 0
##             else:
##                 # print count
##                 incTaskFunc(cnt, enable, reset, n)
##                 count.next = cnt

##     return incTaskGen()


def freeVarTypeError(count, enable, clock, reset, n):
    cnt = intbv(0)[8:]
    def incTaskFunc():
        if enable:
            cnt[:] = (cnt + 1) % n
    def incTaskGen():
        while 1:
            yield posedge(clock), negedge(reset)
            if reset == ACTIVE_LOW:
               cnt[:]= 0
            else:
                incTaskFunc()
    return incTaskGen()


def shadowingSignal(count, enable, clock, reset, n):
    count = Signal(intbv(0)[8:])
    def incTaskGen():
        while 1:
            yield posedge(clock), negedge(reset)
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return incTaskGen()

def internalSignal(count, enable, clock, reset, n):
    a = Signal(bool())
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n
                
def negIntbv(count, enable, clock, reset, n):
    a = intbv(0, min=-2, max=45)
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

def yieldObject1(count, enable, clock, reset, n):
    while 1:
        yield posedge(clock), delay(5)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n
                
def g1(clock):
        yield posedge(clock)
def g2(reset):
        yield negedge(reset)
      
def yieldObject2(count, enable, clock, reset, n):
    while 1:
        yield g1(clock), g2(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

def f1(n):
    if n == 0:
        return 0
    else:
        return f1(n-1)

def f2(n):
    if n == 0:
        return 1
    else:
        return f3(n-1)
    
def f3(n):
    if n == 0:
        return 1
    else:
        return f2(n-1)
      
def recursion1(count, enable, clock, reset, n):
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = f1(n)
                
def recursion2(count, enable, clock, reset, n):
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = f2(n)
      

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
        inc_inst_v = inc_v(count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(inc_inst_ref, inc_inst_v, clk_1, st_1, ch_1)
        return sim

##     def testIncRef(self):
##         """ Check increment operation """
##         sim = self.bench(incRef)
##         sim.run(quiet=1)
        
##     def testIncTask(self):
##         sim = self.bench(incTask)
##         sim.run(quiet=1)
        
##     def testIncTaskFreeVar(self):
##         sim = self.bench(incTaskFreeVar)
##         sim.run(quiet=1)

    def testInternalSignal(self):
        try:
            self.bench(internalSignal)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.TypeInfer)
        else:
            self.fail()
            
    def testShadowingSignal(self):
        try:
            self.bench(shadowingSignal)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.ShadowingSignal)
        else:
            self.fail()
        
    def testFreeVarTypeError(self):
        try:
            self.bench(freeVarTypeError)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.FreeVarTypeError)
        else:
            self.fail()
        
    def testNegIntbv(self):
        try:
            self.bench(negIntbv)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.IntbvSign)
        else:
            self.fail()
            
    def testYield1(self):
        try:
            self.bench(yieldObject1)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.UnsupportedYield)
        else:
            self.fail()
            
    def testYield2(self):
        try:
            self.bench(yieldObject2)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testRecursion1(self):
        try:
            self.bench(recursion1)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testRecursion2(self):
        try:
            self.bench(recursion2)
        except ToVerilogError, e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()


if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

