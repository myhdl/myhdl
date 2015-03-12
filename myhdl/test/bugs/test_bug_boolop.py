from __future__ import absolute_import
from myhdl import *

def gray_counter (clk, reset, enable, gray_count):

    q = Signal(intbv(0)[10:])
    no_ones_below = Signal(intbv(0)[10:])
    q_msb = Signal(bool(0))


    @always_seq(clk.posedge, reset=reset)
    def seq():
        if enable:
            q.next[0] = not q[0]
            for i in range(1, 9):
                q.next[i] = q[i] ^ (q[i-1] and no_ones_below[i-1])
            q.next[8] = q[8] ^ (q_msb and no_ones_below[7])

    @always(q, no_ones_below)
    def comb():
        q_msb.next = q[8] or q[7]
        no_ones_below.next[0] = 1
        for j in range(1, 10):
            no_ones_below.next[j] = no_ones_below[j-1] and not q[j-1]
        gray_count.next[8:] = q[9:1]
            
    return comb, seq
       
clk = Signal(bool(0))
reset = ResetSignal(0, active=0, async=True)
enable = Signal(bool(0))
gray_count = Signal(intbv(0)[8:])

def test_bug_boolop():
    try:
        toVerilog(gray_counter, clk, reset, enable, gray_count)
        toVHDL(gray_counter, clk, reset, enable, gray_count)
    except:
        assert False
