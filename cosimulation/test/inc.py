import myhdl
from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def inc(count, enable, clock, reset, n):
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """

    @always(clock.posedge, reset.negedge)
    def logic():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

    return logic
