from __future__ import absolute_import
import myhdl
from myhdl import *

from timer import timer_sig, timer_var

def test_timer_array(timer):

    MAXVAL = 1234

    clock = Signal(bool())
    reset = Signal(bool())
    flag0 = Signal(bool())
    flag1 = Signal(bool())
    flag2 = Signal(bool())
    flag3= Signal(bool())
    flag4 = Signal(bool())
    flag5 = Signal(bool())
    flag6 = Signal(bool())
    flag7 = Signal(bool())

    dut = [None] * 8

    dut[0] = timer(flag0, clock, reset, MAXVAL)
    dut[1] = timer(flag1, clock, reset, MAXVAL)
    dut[2] = timer(flag2, clock, reset, MAXVAL)
    dut[3] = timer(flag3, clock, reset, MAXVAL)
    dut[4] = timer(flag4, clock, reset, MAXVAL)
    dut[5] = timer(flag5, clock, reset, MAXVAL)
    dut[6] = timer(flag6, clock, reset, MAXVAL)
    dut[7] = timer(flag7, clock, reset, MAXVAL)

    @instance
    def clkgen():
        clock.next = 0
        reset.next = 0
        yield delay(10)
        reset.next = 1
        yield delay(10)
        reset.next = 0
        yield delay(10)
        for i in range(2**24):
            clock.next = not clock
            yield delay(10)

    @instance
    def monitor():
        count = intbv(0, min=0, max=MAXVAL+1)
        seen = False
        while True:
            yield clock.posedge
            if seen:
                if flag0:
                    assert count == MAXVAL
                else:
                    count += 1
            if flag0 or flag1 or flag2 or flag3 or flag4 or flag5 or flag6 or flag7:
                seen = True
                count[:] = 0

    return dut, clkgen, monitor

if __name__ == '__main__':
    sim = Simulation(test_timer_array(timer_var))
    sim.run()
        
