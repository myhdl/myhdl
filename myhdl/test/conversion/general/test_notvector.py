from myhdl import *

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
def notVectorBench0():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
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
   
    i_notVector = notVector0(a, z)


    return instances()


def test_notVector0():
    sim = notVectorBench0()
    sim.run_sim()

def test_notVectorInst():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[8:])
    z   = Signal(modbv(0)[8:])
    
    i_dut = notVector0(a, z)
    assert i_dut.analyze_convert() == 0


def test_notVector0_convert():
    i_dut = notVectorBench0()
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_simulator() == 0
    #assert i_dut.verify_convert() == 0
