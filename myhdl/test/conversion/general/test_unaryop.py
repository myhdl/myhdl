from myhdl import *
import pytest

@block
def notVector0(
    a,
    z,
):
   
    @always_comb
    def outputs():
        z.next = a & ~0x1 


    return instances()

@block
def notVector1(
    a,
    b,
    z,
):
   
    @always_comb
    def outputs():
        z.next = a & ~b 


    return instances()

@block
def notVector2(
    a,
    z,
):
   
    @always_comb
    def outputs():
        z.next = a & +0xfe 


    return instances()

@block
def notVector3(
    a,
    b,
    z,
):
   
    @always_comb
    def outputs():
        z.next = a & +b 


    return instances()

@block
def notVector4(
    a,
    z,
):
   
    @always_comb
    def outputs():
        z.next = a & -0x2 


    return instances()


@block
def notVectorBench0(rev=0):

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    b   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    @instance
    def clkgen():
        clk.next = 1
        for i in range(400):
            yield delay(10)
            clk.next = not clk

    @instance
    def stimulus():
        a.next = 0x0
        if 3 == rev:
            b.next = 0xfe
        elif 5 == rev:
            b.next = 0x2
        else:
            b.next = 0x1
        yield clk.posedge
        yield clk.posedge
        a.next = 0x0
        yield clk.posedge
        a.next = 0x1
        yield clk.posedge
        a.next = 0x2
        yield clk.posedge
        a.next = 0x3
        yield clk.posedge
        a.next = 0xff
        yield clk.posedge


        raise StopSimulation

    @instance
    def check():
        yield clk.posedge
        yield clk.posedge
        yield clk.posedge
        assert z == 0x0
        yield clk.posedge
        assert z == 0x0
        yield clk.posedge
        assert z == 0x2
        yield clk.posedge
        assert z == 0x2
        yield clk.posedge
        assert z == 0xfe
        yield clk.posedge
   
    if 1 == rev:
        i_notVector = notVector1(a, b, z)
    elif 2 == rev:
        i_notVector = notVector2(a, z)
    elif 3 == rev:
        i_notVector = notVector3(a, b, z)
    elif 4 == rev:
        i_notVector = notVector4(a, z)
    else:
        i_notVector = notVector0(a, z)


    return instances()

def test_notVector0():
    sim = notVectorBench0(0)
    sim.run_sim()

def test_notVector0Inst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector0(a, z)
    assert i_dut.analyze_convert() == 0


@pytest.mark.filterwarnings("ignore:Signal is driven")
def test_notVector0_convert():
    i_dut = notVectorBench0(0)
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0

def test_notVector1():
    sim = notVectorBench0(1)
    sim.run_sim()

def test_notVector1Inst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    b   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector1(a, b, z)
    assert i_dut.analyze_convert() == 0


def test_notVector1_convert():
    i_dut = notVectorBench0(1)
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0

def test_notVector2():
    sim = notVectorBench0(2)
    sim.run_sim()

def test_notVector2Inst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector2(a, z)
    assert i_dut.analyze_convert() == 0


@pytest.mark.filterwarnings("ignore:Signal is driven")
def test_notVector2_convert():
    i_dut = notVectorBench0(2)
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0

def test_notVector3():
    sim = notVectorBench0(3)
    sim.run_sim()

def test_notVector3Inst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    b   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector3(a, b, z)
    assert i_dut.analyze_convert() == 0


def test_notVector3_convert():
    i_dut = notVectorBench0(3)
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0

def test_notVector4():
    sim = notVectorBench0(4)
    sim.run_sim()

def test_notVector4Inst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector4(a, z)
    assert i_dut.analyze_convert() == 0


@pytest.mark.filterwarnings("ignore:Signal is driven")
def test_notVector4_convert():
    i_dut = notVectorBench0(4)
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0

