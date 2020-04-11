import pytest

from myhdl import (block, Signal, ResetSignal, intbv, always_seq, always_comb,
                   instance, delay, StopSimulation,)


class Intf(object):

    def __init__(self):
        self.x = Signal(intbv(1, min=-1111, max=1111))
        self.y = Signal(intbv(2, min=-2211, max=2211))
        self.z = Signal(intbv(3, min=-3311, max=3311))


@block
def modify(clock, reset, a):

    intfa = Intf()

    @always_seq(clock.posedge, reset=reset)
    def rtl_inc():
        intfa.x.next = intfa.x + 1
        intfa.y.next = intfa.y + 2
        intfa.z.next = intfa.z + 3

    @always_comb
    def rtl_add():
        a.x.next = intfa.x + 1
        a.y.next = intfa.y + 2
        a.z.next = intfa.z + 3

    return rtl_inc, rtl_add


@block
def use_interfaces(clock, reset, a, b, c):

    intfa = Intf()
    intfaa = Intf()

    mod_inst = modify(clock, reset, intfaa)

    @always_seq(clock.posedge, reset=reset)
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

    return mod_inst, rtl_inc, rtl_combine


@block
def name_conflict_after_replace(clock, reset, a, a_x):
    a_x_0 = [Signal(intbv(0)[len(a_x):]) for _ in range(8)]

    @always_seq(clock.posedge, reset=reset)
    def logic():
        a.x.next = a_x
        a_x.next = a_x_0[1]

    return logic


@pytest.mark.xfail
def test_name_conflict_after_replace():
    clock = Signal(False)
    reset = ResetSignal(0, active=0, isasync=False)
    a = Intf()
    a_x = Signal(intbv(0)[len(a.x):])
    inst = name_conflict_after_replace(clock, reset, a, a_x)
    assert inst.analyze_convert() == 0


@block
def c_testbench():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=False)
    a, b, c = Intf(), Intf(), Intf()

    tb_dut = use_interfaces(clock, reset, a, b, c)

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
            print("a: x=%d y=%d z=%d" % (a.x, a.y, a.z,))
            print("b: x=%d y=%d z=%d" % (b.x, b.y, b.z,))
            print("c: x=%d y=%d z=%d" % (c.x, c.y, c.z,))
            yield clock.posedge

        raise StopSimulation

    return tb_dut, tb_clk, tb_stim


def test_name_conflicts_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=False)
    a, b, c = Intf(), Intf(), Intf()
    inst = use_interfaces(clock, reset, a, b, c)
    assert inst.analyze_convert() == 0


def test_name_conflicts_verify():
    inst = c_testbench()
    assert inst.verify_convert() == 0


if __name__ == '__main__':
    clock = Signal(False)
    reset = ResetSignal(0, active=0, isasync=False)
    a = Intf()
    a_x = Signal(intbv(0)[len(a.x):])
    inst = name_conflict_after_replace(clock, reset, a, a_x)

    inst.convert()
    inst.convert(hdl='VHDL')

