from __future__ import absolute_import
import myhdl
from myhdl import *

from glibc_random import glibc_random

from long_divider import long_divider

def test_longdiv(nrvectors=2**18):
    quotient = Signal(intbv(0)[22:])
    ready = Signal(bool())
    dividend = Signal(intbv(0)[38:])
    divisor = Signal(intbv(0)[16:])
    start = Signal(bool())
    clock = Signal(bool())
    reset = Signal(bool())
    stopped = Signal(bool())

    MAXVAL = 2**22 - 1
    
    dut = long_divider(
        quotient,
        ready,
        dividend,
        divisor,
        start,
        clock,
        reset
        )

    @instance
    def clockgen():
        clock.next = 0
        yield delay(10)
        while not stopped:
            clock.next = not clock
            yield delay(10)
        
    @instance
    def stimulus():
        stopped.next = 0
        yield delay(10)
        random_word = intbv(0)[32:]
        p = intbv(0)[16:]
        q = intbv(0)[22:]
        d = intbv(0)[38:]
        yield clock.negedge
        reset.next = 0
        yield clock.negedge
        reset.next = 1
        yield clock.negedge
        reset.next = 0
        start.next = 0
        yield clock.negedge
        random_word[:] = 94
        for i in range(nrvectors):
            yield clock.negedge
            random_word[:] = glibc_random(random_word)
            p[:] = random_word[16:]
            random_word[:] = glibc_random(random_word)
            q[:] = random_word[22:]
            if p == 0:
                q[:] = MAXVAL
            d[:] = p * q
            dividend.next = d
            divisor.next = p
            start.next = 1
            yield clock.negedge
            start.next = 0
            yield ready.posedge
            """compensate for Verilog's non-determinism"""
            yield delay(1) 
            #print d, p, q, quotient
            assert quotient == q
        stopped.next = 1 
        yield delay(10)
        #raise StopSimulation()
            
    return dut, clockgen, stimulus
    
if __name__ == '__main__':    
    sim = Simulation(test_longdiv())
    sim.run()

