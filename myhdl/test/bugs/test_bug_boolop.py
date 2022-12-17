import myhdl
from myhdl import *

@block
def gray_counter_bug_boolop (clk, reset, enable, gray_count):

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
reset = ResetSignal(0, active=0, isasync=True)
enable = Signal(bool(0))
gray_count = Signal(intbv(0)[8:])

def test_bug_boolop():
    try:
        gray_counter_bug_boolop(clk, reset, enable, gray_count).convert(hdl='Verilog')
        gray_counter_bug_boolop(clk, reset, enable, gray_count).convert(hdl='VHDL')
    except:
        assert False
