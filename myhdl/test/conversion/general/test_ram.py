import os
path = os.path

from myhdl import (block, Signal, intbv, delay, always_comb,
                   always, instance, StopSimulation,
                   conversion
                   )


@block
def ram1(dout, din, addr, we, clk, depth=128):
    """ Simple ram model """

    @instance
    def comb():
        mem = [intbv(0)[8:] for dummy in range(depth)]
        while 1:
            yield clk.posedge
            if we:
                mem[int(addr)][:] = din
            dout.next = mem[int(addr)]

    return comb


@block
def ram_clocked(dout, din, addr, we, clk, depth=128):
    """ Ram model """

    mem = [Signal(intbv(0)[8:]) for __ in range(depth)]

    @instance
    def access():
        while 1:
            yield clk.posedge
            if we:
                mem[int(addr)].next = din
            dout.next = mem[int(addr)]

    return access


@block
def ram_deco1(dout, din, addr, we, clk, depth=128):
    """  Ram model """

    mem = [Signal(intbv(0)[8:]) for __ in range(depth)]

    @instance
    def write():
        while True:
            yield clk.posedge
            if we:
                mem[int(addr)].next = din

    @always_comb
    def read():
        dout.next = mem[int(addr)]

    return write, read


@block
def ram_deco2(dout, din, addr, we, clk, depth=128):
    """  Ram model """

    mem = [Signal(intbv(0)[8:]) for __ in range(depth)]

    @always(clk.posedge)
    def write():
        if we:
            mem[int(addr)].next = din

    @always_comb
    def read():
        dout.next = mem[int(addr)]

    return write, read


@block
def ram2(dout, din, addr, we, clk, depth=128):

    memL = [Signal(intbv()[len(dout):]) for __ in range(depth)]

    @instance
    def wrLogic():
        while 1:
            yield clk.posedge
            if we:
                memL[int(addr)].next = din

    @instance
    def rdLogic():
        while 1:
            yield clk.posedge
            dout.next = memL[int(addr)]

    return wrLogic, rdLogic


@block
def RamBench(ram, depth=128):

    dout = Signal(intbv(0)[8:])
    din = Signal(intbv(0)[8:])
    addr = Signal(intbv(0)[7:])
    we = Signal(bool(0))
    clk = Signal(bool(0))

    mem_inst = ram(dout, din, addr, we, clk, depth)

    @instance
    def stimulus():
        for i in range(depth):
            yield clk.negedge
            din.next = i
            addr.next = i
            we.next = True
            yield clk.negedge
        we.next = False
        for i in range(depth):
            addr.next = i
            yield clk.posedge
            yield delay(1)
            assert dout == i
            print(dout)
        raise StopSimulation()

    @instance
    def clkgen():
        clk.next = 1
        while True:
            yield delay(10)
            clk.next = not clk

    return clkgen, stimulus, mem_inst


def testram_deco1():
    assert conversion.verify(RamBench(ram_deco1)) == 0


def testram_deco2():
    assert conversion.verify(RamBench(ram_deco2)) == 0


def testram_clocked():
    assert conversion.verify(RamBench(ram_clocked)) == 0


def test2():
    assert conversion.verify(RamBench(ram2)) == 0


def test1():
    assert conversion.verify(RamBench(ram1)) == 0
