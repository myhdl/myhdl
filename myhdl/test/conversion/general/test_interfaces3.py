from __future__ import absolute_import

import sys

import pytest

from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

from myhdl import *

from conftest import bug

class Intf1:
    def __init__(self, x):
        self.x = Signal(intbv(0, min=x.min, max=x.max))

class Intf2:
    def __init__(self, y):
        self.y = Signal(intbv(0, min=y.min, max=y.max))

class ZBus:
    def __init__(self, z):
        self.z = Signal(intbv(0, min=z.min, max=z.max))

class Intf3:
    def __init__(self, z):
        self.z = ZBus(z)


class IntfWithConstant1:
    def __init__(self):
        self.const1 = 707
        self.const2 = 3

class IntfWithConstant2:
    def __init__(self):
        self.a = 9
        self.b = 10
        self.c = 1729
        self.more_constants = IntfWithConstant1()


def m_assign(y, x):
    @always_comb
    def assign():
        y.next = x
    return assign

def m_top_assign(x,y,z):
    """
    This module does not test top-level interfaces,
    it only tests intermediate interfaces.
    """
    i1,i2 = Intf1(x), Intf2(y)

    ga1 = m_assign(x, i1.x)  # x = i1.x
    ga2 = m_assign(i2.y, y)  # i2.y = y
    gm1 = m_assign_intf(i1, i2)

    return ga1, ga2, gm1

def m_assign_intf(x, y):
    @always_comb
    def rtl():
        x.x.next = y.y
    return rtl

def c_testbench_one():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]

    tb_dut = m_top_assign(x,y,z)
    @instance
    def tb_stim():
        y.next = 3
        yield delay(10)
        print("x: %d" % (x))
        assert x == 3
        
    return tb_dut, tb_stim
        
def m_top_multi_comb(x,y,z):
    """
    This module does not test top-level interfaces,
    it only tests intermediate interfaces.
    """
    intf = Intf1(x), Intf2(y), Intf3(z)
    x.assign(intf[0].x)    
    intf[1].y.assign(y)
    intf[2].z.z.assign(z)
    gm = m_multi_comb(*intf)
    return gm

def m_multi_comb(x, y, z):
    @always_comb
    def rtl():
        x.x.next = y.y + z.z.z
    return rtl

def c_testbench_two():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]
    tb_dut = m_top_multi_comb(x,y,z)
    @instance
    def tb_stim():
        y.next = 3
        z.next = 2
        yield delay(10)
        print("x: %d" % (x))        
        assert x == 5
        
    return tb_dut, tb_stim
    

def m_top_const(clock, reset, x, y, intf):

    @always_seq(clock.posedge, reset=reset)
    def rtl1():
        v = intf.a**3 + intf.b**3
        x.next = v - intf.c

    @always_comb
    def rtl2():
        y.next = x + intf.more_constants.const1 - \
                 intf.more_constants.const2*235 - 2

    return rtl1, rtl2

def c_testbench_three():
    """
    this will test the use of constants in an inteface
    as well as top-level interface conversion.
    """
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)
    x = Signal(intbv(3, min=-5000, max=5000))
    y = Signal(intbv(4, min=-200, max=200))
    intf = IntfWithConstant2()

    tbdut = m_top_const(clock, reset, x, y, intf)
    
    @instance
    def tbclk():
        clock.next = False
        while True:
            yield delay(3)
            clock.next = not clock
        
    @instance
    def tbstim():
        reset.next = reset.active
        yield delay(33)
        reset.next = not reset.active
        yield clock.posedge
        yield clock.posedge
        print("x: %d" % (x,))
        print("y: %d" % (y,))
        assert x == 0
        assert y == 0
        raise StopSimulation

    return tbdut, tbclk, tbstim

def test_one_analyze():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]
    analyze(m_top_assign, x, y, z)

def test_one_verify():
    assert verify(c_testbench_one) == 0

def test_two_analyze():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]
    analyze(m_top_multi_comb, x, y, z)

def test_two_verify():
    assert verify(c_testbench_two) == 0

def test_three_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)
    x = Signal(intbv(3, min=-5000, max=5000))
    y = Signal(intbv(4, min=-200, max=200))
    intf = IntfWithConstant2()
    analyze(m_top_const, clock, reset, x, y, intf)

def test_three_verify():
    assert verify(c_testbench_three) == 0


if __name__ == '__main__':
    print(sys.argv[1])
    verify.simulator = analyze.simulator = sys.argv[1]
    print("*** verify myhdl simulation")    
    Simulation(c_testbench_one()).run()
    Simulation(c_testbench_two()).run()
    Simulation(c_testbench_three()).run()
    print("*** myhdl simulation ok")    
    print("")

    print("*** myhdl verify conversion")    
    print(verify(c_testbench_one))
    print(verify(c_testbench_two))  
    print(verify(c_testbench_three))  
    print("*** myhdl conversion ok")      
    print("")
