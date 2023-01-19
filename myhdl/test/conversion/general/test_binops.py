from myhdl import *

@block
def binOpsCheck0(
    a,
    b,
    c,
    x,
    y,
    z,
):
   
    @always_comb
    def outputs():
        x.next = a   
        y.next = a | b
        z.next = a | b | c

    return instances()

@block
def binOpsCheck1(
    a,
    x,
    y,
    z,
):
   
    @always_comb
    def outputs():
        x.next = a[0]   
        y.next = a[0] | a[1]
        z.next = a[0] | a[1] | a[2]

    return instances()

@block
def binOpsCheck2(
    a,
    z,
):
   
    @always_comb
    def outputs():
        z[0].next = a[0]   
        z[1].next = a[0] | a[1]
        z[2].next = a[0] | a[1] | a[2]

    return instances()

@block
def binOpsCheckBench0():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[1:])
    b   = Signal(modbv(0)[1:])
    c   = Signal(modbv(0)[1:])
    x   = Signal(modbv(0)[1:])
    y   = Signal(modbv(0)[1:])
    z   = Signal(modbv(0)[1:])
    
    @instance
    def clkgen():
        clk.next = 1
        for i in range(400):
            yield delay(10)
            clk.next = not clk

    @instance
    def stimulus():
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge

        raise StopSimulation

    @instance
    def check():
        yield clk.posedge
        yield clk.posedge
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
   
    i_binOpsCheck = binOpsCheck0(a, b, c, x, y, z)


    return instances()

@block
def binOpsCheckBench1():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[1:])
    b   = Signal(modbv(0)[1:])
    c   = Signal(modbv(0)[1:])
    x   = Signal(False)
    y   = Signal(False)
    z   = Signal(False)
    
    @instance
    def clkgen():
        clk.next = 1
        for i in range(400):
            yield delay(10)
            clk.next = not clk
    
    @instance
    def stimulus():
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge

        raise StopSimulation

    @instance
    def check():
        yield clk.posedge
        yield clk.posedge
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
   
    i_binOpsCheck = binOpsCheck0(a, b, c, x, y, z)

    return instances()

@block
def binOpsCheckBench2():

    clk = Signal(bool(0)) 
    a   = Signal(modbv(0)[2:])
    b   = Signal(modbv(0)[2:])
    c   = Signal(modbv(0)[2:])
    x   = Signal(modbv(0)[2:])
    y   = Signal(modbv(0)[2:])
    z   = Signal(modbv(0)[2:])
    
    @instance
    def clkgen():
        clk.next = 1
        for i in range(400):
            yield delay(10)
            clk.next = not clk


    @instance
    def stimulus():
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x1
        b.next = 0x0
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x1
        c.next = 0x0
        yield clk.posedge
        a.next = 0x1
        b.next = 0x1
        c.next = 0x1
        yield clk.posedge
        a.next = 0x0
        b.next = 0x0
        c.next = 0x0
        yield clk.posedge

        raise StopSimulation

    @instance
    def check():
        yield clk.posedge
        yield clk.posedge
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x1
        assert y == 0x1
        assert z == 0x1
        yield clk.posedge
        assert x == 0x0
        assert y == 0x0
        assert z == 0x0
        yield clk.posedge
   
    i_binOpsCheck = binOpsCheck0(a, b, c, x, y, z)


    return instances()


def test_binOps0():
    sim = binOpsCheckBench0()
    sim.run_sim()

def test_binOps0_convert():
    i_dut = binOpsCheckBench0()
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_simulator() == 0
    #assert i_dut.verify_convert() == 0
    
def test_binOps1():
    sim = binOpsCheckBench1()
    sim.run_sim()

def test_binOps1_convert():
    i_dut = binOpsCheckBench1()
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_simulator() == 0
   
def test_binOps1b_convert():
    a   = Signal(modbv(0)[1:])
    b   = Signal(modbv(0)[1:])
    c   = Signal(modbv(0)[1:])
    x   = Signal(False)
    y   = Signal(False)
    z   = Signal(False)

    i_dut = binOpsCheck0(a, b, c, x, y, z)
    assert i_dut.analyze_convert() == 0
 
def test_binOps1c_convert():
    a   = Signal(intbv(0)[1:])
    b   = Signal(intbv(0)[1:])
    c   = Signal(intbv(0)[1:])
    x   = Signal(False)
    y   = Signal(False)
    z   = Signal(False)

    i_dut = binOpsCheck0(a, b, c, x, y, z)
    assert i_dut.analyze_convert() == 0
    
def test_binOps1d_convert():
    a   = Signal(intbv(0)[3:])
    x   = Signal(False)
    y   = Signal(False)
    z   = Signal(False)

    i_dut = binOpsCheck1(a, x, y, z)
    assert i_dut.analyze_convert() == 0
    
def test_binOps1e_convert():
    a   = Signal(intbv(0)[3:])
    z   = Signal(intbv(0)[3:])

    i_dut = binOpsCheck2(a, z)
    assert i_dut.analyze_convert() == 0
    
def test_binOps2():
    sim = binOpsCheckBench2()
    sim.run_sim()

def test_binOps2_convert():
    i_dut = binOpsCheckBench2()
    assert i_dut.analyze_convert() == 0
    #assert i_dut.verify_convert() == 0
    #assert i_dut.verify_simulator() == 0
