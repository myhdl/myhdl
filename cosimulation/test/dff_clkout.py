import myhdl
from myhdl import *

from dff import dff

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def dff_clkout(clkout, q, d, clk, reset):
    
    DFF_1 = dff(q, d, clkout, reset)

    @instance
    def assign():
        while 1:
            yield clk
            clkout.next = clk
            
    return DFF_1, assign

