from __future__ import absolute_import
import myhdl
from myhdl import *

from timer import timer_sig, timer_var

def test_timer(timer):

    MAXVAL = 1234

    clock = Signal(bool())
    reset = Signal(bool())
    flag = Signal(bool())

    dut = timer(flag, clock, reset, MAXVAL)

    @instance
    def clkgen():
        clock.next = 0
        reset.next = 0
        yield delay(10)
        reset.next = 1
        yield delay(10)
        reset.next = 0
        yield delay(10)
        for i in range(2**25):
            clock.next = not clock
            yield delay(10)

    @instance
    def monitor():
        count = intbv(0, min=0, max=MAXVAL+1)
        seen = False
        while True:
            yield clock.posedge
            if seen:
                if flag:
                    assert count == MAXVAL
                else:
                    count += 1
            if flag:
                seen = True
                count[:] = 0

    return dut, clkgen, monitor

if __name__ == '__main__':
    sim = Simulation(test_timer(timer_var))
    sim.run()
        
