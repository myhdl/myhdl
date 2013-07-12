
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

class MyIntf(object):
    def __init__(self):
        self.x = Signal(intbv(2,min=0,max=16))
        self.y = Signal(intbv(3,min=0,max=18))

def m_one_level(clock,reset,ia,ib):

    @always_seq(clock.posedge,reset=reset)
    def rtl():
        ia.x.next = ib.x + 1
        ia.y.next = ib.y + 1

    return rtl

def m_two_level(clock,reset,ia,ib):

    ic,ie = (MyIntf(),MyIntf,)
    g_one = m_one_level(clock,reset,ic,ie)
    @always_seq(clock.posedge,reset=reset)
    def rtl():
        ia.x.next = ib.x + ic.x
        ia.y.next = ib.y + ic.y

    return g_one, rtl

def _testbench_one():
    clock = Signal(bool(0))
    reset = ResetSignal(0,active=0,async=True)
    ia = MyIntf()
    ib = MyIntf()

    tb_dut = m_one_level(clock,reset,ia,ib)
    
    @always(delay(10))
    def tb_clk():
        clock.next = not clock

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

    return tb_dut, tb_clk, tb_stim

def _testbench_two():
    clock = Signal(bool(0))
    reset = ResetSignal(0,active=0,async=True)
    ia = MyIntf()
    ib = MyIntf()

    tb_dut = m_two_level(clock,reset,ia,ib)
    
    @always(delay(10))
    def tb_clk():
        clock.next = not clock

    @instance
    def tb_stim():
        reset.next = False
        yield delay(17)
        reset.next = True
        yield delay(17)
        for ii in range(7):
            yield clock.posedge
        assert ia.x == 5
        assert ia.y == 6

    return tb_dut, tb_clk, tb_stim        

def test_one_level_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0,active=0,async=True)
    ia = MyIntf()
    ib = MyIntf()
    analyze(m_one_level,clock,reset,ia,ib)

def test_one_level_verify():
    assert verify(_testbench_one) == 0

def test_two_level_verify():
    assert verify(_testbench_two) == 0
