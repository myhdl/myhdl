from __future__ import absolute_import

import sys

from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

from myhdl import *

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
    def __init__(self,z ):
        self.z = ZBus(z)

def m_top_assign(x,y,z):
    """
    This module does not test top-level interfaces,
    it only tests intermediate interfaces.
    """
    i1,i2 = Intf1(x), Intf2(y)
    x.assign(i1.x)
    i2.y.assign(y)
    gm = m_assign_comb(i1, i2)
    return gm

def m_assign_comb(x, y):
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
    

def test_one_analyze():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]
    analyze(m_top_assign,x,y,z)

def test_one_verify():
    assert verify(c_testbench_one) == 0

def test_two_analyze():
    x,y,z = [Signal(intbv(0, min=-8, max=8))
             for _ in range(3)]
    analyze(m_top_multi_comb,x,y,z)

def test_two_verify():
    assert verify(c_testbench_two) == 0

if __name__ == '__main__':
    print(sys.argv[1])
    verify.simulator = analyze.simulator = sys.argv[1]
    print("*** verify myhdl simulation")    
    Simulation(c_testbench_one()).run()
    Simulation(c_testbench_two()).run()
    print("*** myhdl simulation ok")    
    print(verify(c_testbench_one))
    print(verify(c_testbench_two))    
