from myhdl import *

from random_generator import random_generator

from long_divider import long_divider

def test_longdiv():
    random_word = Signal(intbv(0)[38:])
    enable = Signal(bool())
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

    randgen = random_generator(
        random_word,
        enable,
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
        p = intbv(0)[16:]
        q = intbv(0)[22:]
        d = intbv(0)[38:]
        enable.next = 0
        yield clock.negedge
        reset.next = 0
        yield clock.negedge
        reset.next = 1
        yield clock.negedge
        reset.next = 0
        start.next = 0
        yield clock.negedge
        for i in range(2**18):
            yield clock.negedge
            enable.next = 1
            yield clock.negedge
            enable.next = 0
            p[:] = random_word[38:22]
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
            #print d, p, q, quotient
            assert quotient == q
        stopped.next = 1 
	yield delay(10)
        #raise StopSimulation()
            
    return dut, randgen, clockgen, stimulus
    
if __name__ == '__main__':    
    sim = Simulation(test_longdiv())
    sim.run()

