from __future__ import absolute_import
from myhdl import *
from myhdl.conversion import analyze

def bug_3577799 (
        clk,
        reset_clk,
        wr_data,
        wr,
        rd_data
    ):

    @instance
    def seq():
        count = 0
        while True:
            yield clk.posedge
            if reset_clk:
                count = 0
            else:
                if wr:
                    if count < depth:
                        rd_data.next = wr_data
                        count = count + 1
                
    return seq

depth = 8
clk = Signal(bool(0))
reset_clk = Signal(bool(0))
wr_data = Signal(intbv(0)[16:])
wr = Signal(bool(0))
rd_data = Signal(intbv(0)[16:])

def test_bug_3577799():
    assert analyze(bug_3577799, clk, reset_clk, wr_data, wr, rd_data) == 0
