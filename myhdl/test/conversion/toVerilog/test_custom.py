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

from myhdl import ConversionError
from myhdl.conversion._misc import _error


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


def incGen(count, enable, clock, reset, n):
    """ Generator with __verilog__ is not permitted """
    @instance
    def logic():
        __verilog__ = "Template string"
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
        # make it fail in conversion
        import types
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

    count.driven = "reg"

    __verilog__ = \
"""
always @(posedge %(clock)s, negedge %(reset)s) begin
    if (reset == 0) begin
        %(count)s <= 0;
    end
    else begin
        if (enable) begin
            %(count)s <= (%(count)s + 1) %% %(n)s;
        end
    end
end
"""
                
    return incProcess


def incErr(count, enable, clock, reset, n):
    
    @always(clock.posedge, reset.negedge)
    def incProcess():
        # make it fail in conversion
        import types
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

    count.driven = "reg"

    __verilog__ = \
"""
always @(posedge %(clock)s, negedge %(reset)s) begin
    if (reset == 0) begin
        %(count)s <= 0;
    end
    else begin
        if (enable) begin
            %(count)s <= (%(countq)s + 1) %% %(n)s;
        end
    end
end
"""
                
    return incProcess



def inc_comb(nextCount, count, n):

    @always_comb
    def logic():
        # make if fail in conversion
        import types
        nextCount.next = (count + 1) % n

    nextCount.driven = "wire"

    __verilog__ =\
"""
assign %(nextCount)s = (%(count)s + 1) %% %(n)s;
"""

    return logic

def inc_seq(count, nextCount, enable, clock, reset):

    @always(clock.posedge, reset.negedge)
    def logic():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if (enable):
                count.next = nextCount

    count.driven = "reg"

    __verilog__ = \
"""
always @(posedge %(clock)s, negedge %(reset)s) begin
    if (reset == 0) begin
        %(count)s <= 0;
    end
    else begin
        if (enable) begin
            %(count)s <= %(nextCount)s;
        end
    end
end
"""
    # return nothing - cannot be simulated
    return []

def inc2(count, enable, clock, reset, n):
    
    nextCount = Signal(intbv(0, min=0, max=n))

    comb = inc_comb(nextCount, count, n)
    seq = inc_seq(count, nextCount, enable, clock, reset)

    return comb, seq


def inc3(count, enable, clock, reset, n):
    inc2_inst = inc2(count, enable, clock, reset, n)
    return inc2_inst


      
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
                
    def bench(self, incRef, incVer):

        m = 8
        n = 2 ** m
 
        count = Signal(intbv(0)[m:])
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]

        inc_inst_ref = incRef(count, enable, clock, reset, n=n)
        inc_inst = toVerilog(incVer, count, enable, clock, reset, n=n)
        # inc_inst = inc(count, enable, clock, reset, n=n)
        inc_inst_v = inc_v(incVer.__name__, count_v, enable, clock, reset)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(inc_inst_ref, inc_inst_v, clk_1, st_1, ch_1)
        return sim

    def testIncRefIncRef(self):
        """ Check increment operation """
        sim = self.bench(incRef, incRef)
        sim.run(quiet=1)
        
    def testIncRefInc(self):
        sim = self.bench(incRef, inc)
        sim.run(quiet=1)
        
    def testIncInc(self):
        sim = self.bench(inc, inc)
        sim.run(quiet=1)

    def testIncRefInc2(self):
        sim = self.bench(incRef, inc2)
        sim.run(quiet=1)

    def testIncRefInc3(self):
        sim = self.bench(incRef, inc3)
        sim.run(quiet=1)

    def testIncGen(self):
        m = 8
        n = 2 ** m
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]
        try:
            inc_inst = toVerilog(incGen, count_v, enable, clock, reset, n=n)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()

    def testIncErr(self):
        m = 8
        n = 2 ** m
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]
        try:
            inc_inst = toVerilog(incErr, count_v, enable, clock, reset, n=n)
        except ConversionError as e:
            pass
        else:
            self.fail()

          
   
        
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

