from __future__ import generators
from myhdl import Signal, intbv, posedge, negedge

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def dff(q, d, clk, reset):
    """ D flip-flop.
    
    q -- output
    d -- input 
    clock -- clock input
    reset -- asynchronous reset input
    """
    while 1:
        yield posedge(clk), negedge(reset)
        if reset == ACTIVE_LOW:
            q.next = 0
        else:
            q.next = d

