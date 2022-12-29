import myhdl
from myhdl import *

@block
def issue_18(dout, din, addr, we, clk, depth=128):
    """  Ram model """
    
    mem = [Signal(intbv(0)[8:]) for i in range(depth)]
    
    @always(clk.posedge)
    def write():
        if we:
            mem[addr].next = din
                
    @always_comb
    def read():
        dout.next = mem[addr]

    return write, read


dout = Signal(intbv(0)[8:])
dout_v = Signal(intbv(0)[8:])
din = Signal(intbv(0)[8:])
addr = Signal(intbv(0)[7:])
we = Signal(bool(0))
clk = Signal(bool(0))

def test_issue_18():
    toVHDL.std_logic_ports = True
    assert issue_18(dout, din, addr, we, clk).analyze_convert() == 0

