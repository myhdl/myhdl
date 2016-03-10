from random import randrange
import seven_segment
import myhdl
from myhdl import *
from bcd2led import bcd2led


PERIOD = 10

def bench():
    
    led = Signal(intbv(0)[7:])
    bcd = Signal(intbv(0)[4:])
    clock = Signal(bool(0))
    
    dut = bcd2led(led, bcd, clock)

    @always(delay(PERIOD//2))
    def clkgen():
        clock.next = not clock

    @instance
    def check():
        for i in range(100):
            bcd.next = randrange(10)
            yield clock.posedge
            yield clock.negedge
            expected = int(seven_segment.encoding[int(bcd)], 2)
            assert led == expected
        raise StopSimulation

    return dut, clkgen, check


def test_bench():
    sim = Simulation(bench())
    sim.run()

    

