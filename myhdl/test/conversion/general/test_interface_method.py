from __future__ import absolute_import

import sys

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

class simple_interface(object):
    def __init__(self):
        self.x = Signal(intbv(0, min=0, max=16))

    def inc(self):
        return self.x + 1

@block
def simple_do(clk, reset):

    i = simple_interface()
    @always_seq(clk.posedge, reset = reset)
    def inc_caller():
        i.inc()

@block
def testbench_one():
    clk = Signal(bool(0))
    reset = ResetSignal(0, active = 0, async = True)

    tb_dut = simple_do(clk, reset)

    @instance
    def tb_clk():
        clk.next = False
        yield delay(10)
        while True:
            clk.next = not clk
            yield delay(10)

    @instance
    def tb_stim():
        reset.next = False
        yield delay(17)
        reset.next = True
        yield delay(17)
        for n in range(7):
            yield clock.posedge
        assert i.x == 3
        print("%d"%(i.x))
        raise StopSimulation

    return tb_dut, tb_clk, tb_stim

@block
def test_simple_do_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active = 0, async = True)
    analyze(simple_do(clock,reset))

@block
def test_simple_do_verify():
    #TODO: implement this
    pass


if __name__ == '__main__':
    #TODO: implement this
    pass
