from __future__ import absolute_import

import sys

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify


class interface_simple(object):
    def __init__(self):
        self.x = Signal(intbv(0, min=0, max=16))

    def inc(self):
        return self.x + 1


@block
def do_simple(clk, reset):

    i = interface_simple()

    @always_seq(clk.posedge, reset=reset)
    def inc_caller():
        i.inc()


@block
def testbench_one():
    clk = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)

    tb_dut = do_simple(clk, reset)

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
            yield clk.posedge
        assert i.x == 3
        print("%d" % (i.x))
        raise StopSimulation

    return tb_dut, tb_clk, tb_stim


@block
def test_do_simple_analyze():
    clk = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)
    analyze(do_simple(clk, reset))


@block
def test_do_simple_verify():
    assert verify(testbench_one()) == 0


if __name__ == '__main__':
    print(sys.argv[1])
    verify.simulator = analyze.simulator = sys.argv[1]
    Simulation(testbench_one()).run()
    print(verify(testbench_one))
