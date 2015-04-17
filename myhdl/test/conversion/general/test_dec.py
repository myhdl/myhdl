from __future__ import absolute_import
import os
path = os.path
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl.conversion import verify

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
        if cnt == -n:
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
                cnt[:] = n-1
            else:
                cnt[:] = cnt - 1

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



def DecBench(dec):
    
    m = 8
    n = 2 ** (m-1)

    count = Signal(intbv(0, min=-n, max=n))
    count_v = Signal(intbv(0, min=-n, max=n))
    enable = Signal(bool(0))
    clock, reset = [Signal(bool(1)) for i in range(2)]

    @instance
    def clockGen():
        yield delay(10)
        clock.next = 0
        while 1:
            yield delay(10)
            clock.next = not clock

    enables = tuple([min(1, randrange(5)) for i in range(1000)])
    @instance
    def stimulus():
        reset.next = INACTIVE_HIGH
        yield clock.negedge
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = 1
            yield clock.negedge
        for i in range(len(enables)):
            enable.next = enables[i]
            yield clock.negedge
        raise StopSimulation

    @instance
    def check():
        yield reset.negedge
        yield reset.posedge
        print(count)
        while 1:
            yield clock.posedge
            yield delay(1)
            print(count)

    dec_inst = dec(count, enable, clock, reset, n=n)

    return dec_inst, clockGen, stimulus, check



def testDecRef():
    assert verify(DecBench, decRef) == 0
    
def testDec():
    assert verify(DecBench, dec) == 0
    
def testDecFunc():
    assert verify(DecBench, decFunc) == 0
    
def testDecTask():
    assert verify(DecBench, decTask) == 0

    
    
## def testDecTaskFreeVar():
##     assert verify(DecBench, decTaskFreeVar) == 0

##     def testDecRef(self):
##         sim = self.bench(decRef)
##         sim.run(quiet=1)
        
##     def testDec(self):
##         sim = self.bench(dec)
##         sim.run(quiet=1)
        
##     def testDecFunc(self):
##         sim = self.bench(decFunc)
##         sim.run(quiet=1)

## signed inout in task doesn't work yet in Icarus
##     def testDecTask(self):
##         sim = self.bench(decTask)
##         sim.run(quiet=1)
        
##     def testDecTaskFreeVar(self):
##         sim = self.bench(decTaskFreeVar)
##         sim.run(quiet=1)            
            

    

    
        


                

        

