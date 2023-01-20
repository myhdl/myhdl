import sys
from myhdl import *
import pytest

@block
def mux4a(
    sel, 
    in0, 
    in1, 
    in2, 
    in3, 
    out0
):
    
    @always_comb
    def rtl():
        if sel == 0:
            out0.next = in0
        elif sel == 1:
            out0.next = in1
        elif sel == 2:
            out0.next = in2
        else:
            out0.next = in3

    return instances()

@block
def mux4b(sel, in0, in1, in2, in3, out0):
    @always_comb
    def rtl():
            pass
            match sel:
                case 0:
                    out0.next = in0
                case 1:
                    out0.next = in1
                case 2:
                    out0.next = in2
                case _:
                    out0.next = in3
    return instances()

@block
def muxBench0(setup=0):

    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in2  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 
    
    @instance
    def clkgen():
        clk.next = 1
        for i in range(400):
            yield delay(10)
            clk.next = not clk

    @instance
    def stimulus():
        sel.next = 0x0
        in0.next = 0xa
        in1.next = 0xb
        in2.next = 0xc
        in3.next = 0xd
        yield clk.posedge
        yield clk.posedge
        sel.next = 0x1
        yield clk.posedge
        sel.next = 0x2
        yield clk.posedge
        sel.next = 0x3
        yield clk.posedge
        sel.next = 0x0
        yield clk.posedge

        raise StopSimulation

    @instance
    def check():
        yield clk.posedge
        yield clk.posedge
        assert out0 == 0xa
        yield clk.posedge
        assert out0 == 0xb
        yield clk.posedge
        assert out0 == 0xc
        yield clk.posedge
        assert out0 == 0xd
        yield clk.posedge
        assert out0 == 0xa
        yield clk.posedge
   
    if 0 == setup:
        i_mux = mux4a(sel, in0, in1, in2, in3, out0)
    else:
        i_mux = mux4b(sel, in0, in1, in2, in3, out0)

    return instances()

def test_mux4a_convert():
    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in2  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 

    i_dut = mux4a(sel, in0, in1, in2, in3, out0)
    assert i_dut.analyze_convert() == 0

def test_muxBench0():
    sim = muxBench0(0)
    sim.run_sim()
    
def test_muxBench0_convert():
    i_dut = muxBench0(0)
    assert i_dut.analyze_convert() == 0

@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_mux4b_convert():
    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in2  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 

    i_dut = mux4b(sel, in0, in1, in2, in3, out0)
    assert i_dut.analyze_convert() == 0

@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_muxBench1():
    sim = muxBench0(1)
    sim.run_sim()

@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_muxBench1_convert():
    i_dut = muxBench0(1)
    assert i_dut.analyze_convert() == 0


