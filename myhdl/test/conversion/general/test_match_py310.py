import sys
from myhdl import *
import pytest

#SELOPTS = enum('SEL0', 'SEL1', 'SEL2', 'SEL3')

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
def mux4c(sel, in0, in1, in3, out0):
    @always_comb
    def rtl():
        match sel:
            case 0:
                out0.next = in0
            case 1 | 2:
                out0.next = in1
            case _:
                out0.next = in3
    return instances()

t_opts = enum('SEL0', 'SEL1', 'SEL2', 'SEL3')

@block
def enumMux4a(
    sel, 
    in0, 
    in1, 
    in2, 
    in3, 
    out0,
):
    
    sel_enum = Signal(t_opts.SEL0)
    
    @always_comb
    def mapping():
        if 0 == sel:
            sel_enum.next = t_opts.SEL0
        elif 1 == sel:
            sel_enum.next = t_opts.SEL1
        elif 2 == sel:
            sel_enum.next = t_opts.SEL2
        elif 3 == sel:
            sel_enum.next = t_opts.SEL3
    
    
    @always_comb
    def rtl():
        if sel_enum == t_opts.SEL0:
            out0.next = in0
        elif sel_enum == t_opts.SEL1:
            out0.next = in1
        elif sel_enum == t_opts.SEL2:
            out0.next = in2
        elif sel_enum == t_opts.SEL3:
            out0.next = in3

    return instances()

@block
def enumMux4b(
    sel, 
    in0, 
    in1, 
    in2, 
    in3, 
    out0,
):
    sel_enum = Signal(t_opts.SEL0)
    
    @always_comb
    def mapping():
        if 0 == sel:
            sel_enum.next = t_opts.SEL0
        elif 1 == sel:
            sel_enum.next = t_opts.SEL1
        elif 2 == sel:
            sel_enum.next = t_opts.SEL2
        elif 3 == sel:
            sel_enum.next = t_opts.SEL3
    
    
    @always_comb
    def rtl():
        match sel_enum:
            case t_opts.SEL0:
                out0.next = in0
            case t_opts.SEL1:
                out0.next = in1
            case t_opts.SEL2:
                out0.next = in2
            case _:
                out0.next = in3        

    return instances()

t_fsma_opts = enum('IDLE', 'READ', 'WRITE', 'ERROR')

@block
def fsm4a(
    clk, 
    rst, 
    rd, 
    wr, 
):
    smp = Signal(t_fsma_opts.IDLE)
    
    @always(clk.posedge)
    def rtl():
        
        if rst:
            smp.next =  t_fsma_opts.IDLE
        else:
            match smp:
                case t_fsma_opts.IDLE:
                    smp.next =  t_fsma_opts.IDLE
                    if rd:
                        smp.next =  t_fsma_opts.READ
                    if wr:
                        smp.next =  t_fsma_opts.WRITE
                case t_fsma_opts.READ:
                    smp.next =  t_fsma_opts.IDLE
                case t_fsma_opts.WRITE:
                    smp.next =  t_fsma_opts.IDLE
                case _:
                    smp.next =  t_fsma_opts.IDLE

    return instances()

@block
def fsm4b(
    clk, 
    a, 
    b, 
    c, 
    z, 
):
    
    @always(clk.posedge)
    def rtl():
        match concat(a,b,c):
            case intbv(0b111) :
                z.next = 0x6
            case intbv(0b101) | intbv(0b110) :
                z.next = 0x7
            case _:
                z.next = 0x0

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
    elif 1 == setup:
        i_mux = mux4b(sel, in0, in1, in2, in3, out0)
    elif 2 == setup:
        i_mux = enumMux4a(sel, in0, in1, in2, in3, out0)
    else:
        i_mux = enumMux4b(sel, in0, in1, in2, in3, out0)

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

#@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
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

#@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_mux4b_convert():
    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 

    i_dut = mux4c(sel, in0, in1, in3, out0)
    assert i_dut.analyze_convert() == 0

#@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_muxBench1():
    sim = muxBench0(1)
    sim.run_sim()

#@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_muxBench1_convert():
    i_dut = muxBench0(1)
    assert i_dut.analyze_convert() == 0

def test_muxBench2():
    sim = muxBench0(2)
    sim.run_sim()

def test_muxBench2_convert():
    i_dut = muxBench0(2)
    assert i_dut.analyze_convert() == 0

def test_enumMux4a_convert():
    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in2  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 

    i_dut = enumMux4a(sel, in0, in1, in2, in3, out0)
    assert i_dut.analyze_convert() == 0

def test_muxBench3():
    sim = muxBench0(3)
    sim.run_sim()

def test_enumMux4b_convert():
    clk  = Signal(bool(0)) 
    sel  = Signal(intbv(0)[2:])
    in0  = Signal(intbv(0)[4:]) 
    in1  = Signal(intbv(0)[4:]) 
    in2  = Signal(intbv(0)[4:]) 
    in3  = Signal(intbv(0)[4:]) 
    out0 = Signal(intbv(0)[4:]) 

    i_dut = enumMux4b(sel, in0, in1, in2, in3, out0)
    assert i_dut.analyze_convert() == 0


def test_fsm4a_convert():
    clk = Signal(bool(0)) 
    rst = Signal(intbv(0)[1:]) 
    rd  = Signal(intbv(0)[1:]) 
    wr  = Signal(intbv(0)[1:]) 


    i_dut = fsm4a(clk, rst, rd, wr)
    assert i_dut.analyze_convert() == 0

def test_fsm4b_convert():
    clk = Signal(bool(0)) 
    a   = Signal(intbv(0)[1:]) 
    b   = Signal(intbv(0)[1:]) 
    c   = Signal(intbv(0)[1:]) 
    z   = Signal(intbv(0)[3:])


    i_dut = fsm4b(clk, a, b, c, z)
    assert i_dut.analyze_convert() == 0

