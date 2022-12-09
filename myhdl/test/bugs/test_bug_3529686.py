import myhdl
from myhdl import *

@block
def bug_3529686(clr, clk, run, ack, serialout):

    @always(clk.posedge, clr.posedge)
    def fsm():
        if (clr == 0):
            serialout.next = 0 
        else:
            if (ack == 0):
                serialout.next = 0
            elif (run == 1):
                serialout.next = 1

    return fsm 


clr, clk, run, ack, serialout = [Signal(bool()) for i in range(5)]


def test_bug_3529686():
    try:
        bug_3529686(clr, clk, run, ack, serialout).convert(hdl='VHDL')
    except:
        assert False
