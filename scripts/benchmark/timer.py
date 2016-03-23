from __future__ import absolute_import
import myhdl
from myhdl import *

def timer_sig(flag, clock, reset, MAXVAL):

    count = Signal(intbv(0, min=0, max=MAXVAL+1))

    @always (clock.posedge, reset.posedge)
    def logic():
        if reset == 1:
            count.next = 0
        else:
            flag.next = 0
            if count == MAXVAL:
                flag.next = 1
                count.next = 0
            else:
                count.next = count + 1

    return logic


def timer_var(flag, clock, reset, MAXVAL):

    @instance
    def logic():
        count = intbv(0, min=0, max=MAXVAL+1)
        while True:
            yield clock.posedge, reset.posedge
            if reset == 1:
                count[:] = 0
            else:
                flag.next = 0
                if count == MAXVAL:
                    flag.next = 1
                    count[:] = 0
                else:
                    count += 1

    return logic


