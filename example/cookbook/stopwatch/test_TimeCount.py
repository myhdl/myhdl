from random import randrange

import myhdl
from myhdl import *

from TimeCount import TimeCount

LOW, HIGH = bool(0), bool(1)

MAX_COUNT = 6 * 10 * 10
PERIOD = 10

def bench():

    """ Unit test for time counter. """

    tens, ones, tenths = [Signal(intbv(0)[4:]) for i in range(3)]
    startstop, reset, clock = [Signal(LOW) for i in range(3)]

    dut = TimeCount(tens, ones, tenths, startstop, reset, clock)
    
    count = Signal(0)
    counting = Signal(False)

    @always(delay(PERIOD//2))
    def clkgen():
        clock.next = not clock

##     @always(reset.posedge)
##     def clear():
##         counting.next = False
##         count.next = 0
            
##     @always(startstop.posedge)
##     def go():
##         counting.next = not counting

    @always(startstop.posedge, reset.posedge)
    def action():
        if reset:
            counting.next = False
            count.next = 0
        else:
            counting.next = not counting      

    @always(clock.posedge)
    def counter():
        if counting:
            count.next = (count + 1) % MAX_COUNT
            
    @always(clock.negedge)
    def monitor():
        assert ((tens*100) + (ones*10) + tenths) == count

    @instance
    def stimulus():
        for maxInterval in (100*PERIOD, 2*MAX_COUNT*PERIOD):
            for sig in (reset, startstop,
                        reset, startstop, startstop,
                        reset, startstop, startstop, startstop,
                        reset, startstop, reset, startstop, startstop, startstop):
               yield delay(randrange(10*PERIOD, maxInterval))
               yield clock.negedge # sync to avoid race condition
               sig.next = HIGH
               yield delay(100)
               sig.next = LOW
        raise StopSimulation
  
    return dut, clkgen, action, counter, monitor, stimulus


def test_bench():
    sim = Simulation(bench())
    sim.run()

def convert():
    tens, ones, tenths = [Signal(intbv(0)[4:]) for i in range(3)]
    startstop, reset, clock = [Signal(LOW) for i in range(3)]

    toVerilog(TimeCount, tens, ones, tenths, startstop, reset, clock)
    toVHDL(TimeCount, tens, ones, tenths, startstop, reset, clock)

convert()
