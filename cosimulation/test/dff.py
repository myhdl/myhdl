import myhdl
from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def dff(q, d, clk, reset):
    """ D flip-flop.
    
    q -- output
    d -- input 
    clock -- clock input
    reset -- asynchronous reset input
    """

    @always(clk.posedge, reset.negedge)
    def logic():
        if reset == ACTIVE_LOW:
            q.next = 0
        else:
            q.next = d

    return logic



