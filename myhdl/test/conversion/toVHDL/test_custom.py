from __future__ import absolute_import
import os
path = os.path

import random
from random import randrange
random.seed(2)

from myhdl import *

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
    """ Generator with __vhdl__ is not permitted """
    @instance
    def logic():
        __vhdl__ = "Template string"
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

    __vhdl__ = \
"""
process (%(clock)s, %(reset)s) begin
    if (reset = '0') then
        %(count)s <= (others => '0');
    elsif rising_edge(%(clock)s) then
        if (enable = '1') then
            %(count)s <= (%(count)s + 1) mod %(n)s;
        end if;
    end if;
end process;
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

    __vhdl__ = \
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

    __vhdl__ =\
"""
%(nextCount)s <= (%(count)s + 1) mod %(n)s;
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

    count.driven = True

    __vhdl__ = \
"""
process (%(clock)s, %(reset)s) begin
    if (reset = '0') then
        %(count)s <= (others => '0');
    elsif rising_edge(%(clock)s) then
        if (enable = '1') then
            %(count)s <= %(nextCount)s;
        end if;
    end if;
end process;
"""
    
    return logic

def inc2(count, enable, clock, reset, n):
    
    nextCount = Signal(intbv(0, min=0, max=n))

    comb = inc_comb(nextCount, count, n)
    seq = inc_seq(count, nextCount, enable, clock, reset)

    return comb, seq


def inc3(count, enable, clock, reset, n):
    inc2_inst = inc2(count, enable, clock, reset, n)
    return inc2_inst


def clockGen(clock):
    @instance
    def logic():
        clock.next = 1
        while 1:
            yield delay(10)
            clock.next = not clock
    return logic

NRTESTS = 1000

ENABLES = tuple([min(1, randrange(5)) for i in range(NRTESTS)])

def stimulus(enable, clock, reset):
    @instance
    def logic():
        reset.next = INACTIVE_HIGH
        yield clock.negedge
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(NRTESTS):
            enable.next = 1
            yield clock.negedge
        for i in range(NRTESTS):
            enable.next = ENABLES[i]
            yield clock.negedge
        raise StopSimulation
    return logic


def check(count, enable, clock, reset, n):
    @instance
    def logic():
        expect = 0
        yield reset.posedge
        # assert count == expect
        print count
        while 1:
            yield clock.posedge
            if enable:
                expect = (expect + 1) % n
            yield delay(1)
            # print "%d count %s expect %s count_v %s" % (now(), count, expect, count_v)
            # assert count == expect
            print count
    return logic


def customBench(inc):

    m = 8
    n = 2 ** m

    count = Signal(intbv(0)[m:])
    enable = Signal(bool(0))
    clock, reset = [Signal(bool(1)) for i in range(2)]

    inc_inst = inc(count, enable, clock, reset, n=n)
    clk_1 = clockGen(clock)
    st_1 = stimulus(enable, clock, reset)
    ch_1 = check(count, enable, clock, reset, n=n)

    return inc_inst, clk_1, st_1, ch_1



def testIncRef():
    assert conversion.verify(customBench, incRef) == 0

def testInc():
    assert conversion.verify(customBench, inc) == 0
    
def testInc2():
    assert conversion.verify(customBench, inc2) == 0
    
def testInc3():
    assert conversion.verify(customBench, inc3) == 0

def testIncGen():
    try:
        assert conversion.verify(customBench, incGen) == 0
    except ConversionError as e:
        pass
    else:
        assert False
        
def testIncErr():
    try:
        assert conversion.verify(customBench, incErr) == 0
    except ConversionError as e:
        pass
    else:
        assert False




    

    
        


                

        

