from myhdl import (block, Signal, ResetSignal, intbv, always_seq,
                   instance, delay, StopSimulation, )


class MyIntf(object):
    def __init__(self):
        self.x = Signal(intbv(2, min=0, max=16))
        self.y = Signal(intbv(3, min=0, max=18))


@block
def one_level(clock, reset, ia, ib):

    @always_seq(clock.posedge, reset=reset)
    def rtl():
        ia.x.next = ib.x + 1
        ia.y.next = ib.y + 1

    return rtl


@block
def two_level(clock, reset, ia, ib):

    ic, ie = MyIntf(), MyIntf()
    one_inst = one_level(clock, reset, ic, ie)

    @always_seq(clock.posedge, reset=reset)
    def rtl():
        ia.x.next = ib.x + ic.x
        ia.y.next = ib.y + ic.y

    return one_inst, rtl


@block
def c_testbench_one():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)
    ia, ib = MyIntf(), MyIntf()

    tb_dut = one_level(clock, reset, ia, ib)

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
        yield delay(17)
        reset.next = True
        yield delay(17)
        for ii in range(7):
            yield clock.posedge
        assert ia.x == 3
        assert ia.y == 4
        print("%d %d %d %d" % (ia.x, ia.y, ib.x, ib.y))
        raise StopSimulation

    return tb_dut, tb_clk, tb_stim


@block
def c_testbench_two():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)
    ia, ib = MyIntf(), MyIntf()

    tb_dut = two_level(clock, reset, ia, ib)

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
        yield delay(17)
        reset.next = True
        yield delay(17)
        for ii in range(7):
            yield clock.posedge
        assert ia.x == 5
        assert ia.y == 7
        print("%d %d %d %d" % (ia.x, ia.y, ib.x, ib.y))
        raise StopSimulation

    return tb_dut, tb_clk, tb_stim


def test_one_level_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)
    ia, ib = MyIntf(), MyIntf()
    inst = one_level(clock, reset, ia, ib)
    assert inst.analyze_convert() == 0


def test_one_level_verify():
    inst = c_testbench_one()
    assert inst.verify_convert() == 0


def test_two_level_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)
    ia, ib = MyIntf(), MyIntf()
    inst = two_level(clock, reset, ia, ib)
    assert inst.analyze_convert() == 0


def test_two_level_verify():
    inst = c_testbench_two()
    assert inst.verify_convert() == 0
