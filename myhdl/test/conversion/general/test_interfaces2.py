from __future__ import absolute_import

import sys

from myhdl import *
from myhdl.conversion import analyze,verify

class Intf(object):
    def __init__(self):
        self.x = Signal(intbv(1,min=-1111,max=1111))
        self.y = Signal(intbv(2,min=-2211,max=2211))
        self.z = Signal(intbv(3,min=-3311,max=3311))

def m_modify(clock,reset,a):

    intfa = Intf()

    @always_seq(clock.posedge,reset=reset)
    def rtl_inc():
        intfa.x.next = intfa.x + 1
        intfa.y.next = intfa.y + 2
        intfa.z.next = intfa.z + 3

    @always_comb
    def rtl_add():
        a.x.next = intfa.x + 1
        a.y.next = intfa.y + 2
        a.z.next = intfa.z + 3

    return rtl_inc,rtl_add

def m_test_intf(clock,reset,a,b,c):

    intfa = Intf()
    intfaa = Intf()

    gen_mod = m_modify(clock,reset,intfaa)

    @always_seq(clock.posedge,reset=reset)
    def rtl_inc():
        intfa.x.next = intfa.x - 1
        intfa.y.next = intfa.y - 2
        intfa.z.next = intfa.z - 3

        b.x.next = b.x + 1
        b.y.next = b.y + 2
        b.z.next = b.z + 3

        c.x.next = c.x + 1
        c.y.next = c.y + 2
        c.z.next = c.z + 3

    @always_comb
    def rtl_combine():
        a.x.next = intfaa.x + 1
        a.y.next = intfaa.y + 2
        a.z.next = intfaa.z + 3

    return gen_mod,rtl_inc,rtl_combine


def name_conflict_after_replace(clock, reset, a, a_x):
    a_x_0 = [Signal(intbv(0)[len(a_x):]) for i in range(8)]

    @always_seq(clock.posedge, reset=reset)
    def logic():
        a.x.next = a_x
        a_x.next = a_x_0[1]

    return logic


def test_name_conflict_after_replace():
    clock = Signal(False)
    reset = ResetSignal(0, active=0, async=False)
    a = Intf()
    a_x = Signal(intbv(0)[len(a.x):])
    assert conversion.analyze(name_conflict_after_replace, clock, reset, a, a_x) == 0


def c_testbench():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=False)
    a,b,c = (Intf(),Intf(),Intf(),)

    tb_dut = m_test_intf(clock,reset,a,b,c)

    @instance
    def tb_clk():
        clock.next = False
        yield delay(10)
        while True:
            clock.next = not clock
            yield delay(10)

    @instance
    def tb_stim():
        reset.next = False
        yield delay(23)
        reset.next = True
        yield delay(33)
        for ii in range(17):
            print("a: x=%d y=%d z=%d"%(a.x,a.y,a.z))
            print("b: x=%d y=%d z=%d"%(b.x,b.y,b.z))
            print("c: x=%d y=%d z=%d"%(c.x,c.y,c.z))
            yield clock.posedge

        raise StopSimulation

    return tb_dut,tb_clk,tb_stim

def test_name_conflicts_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=False)
    a,b,c = (Intf(),Intf(),Intf(),)
    analyze(m_test_intf,clock,reset,a,b,c)

def test_name_conflicts_verify():
    assert verify(c_testbench) == 0

if __name__ == '__main__':
    verify.simulator = analyze.simulator = sys.argv[1]
    Simulation(c_testbench()).run()
    print(verify(c_testbench))
