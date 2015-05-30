from __future__ import absolute_import
import os
path = os.path
from random import randrange

from myhdl import *

D = 256

ROM = tuple([randrange(D) for i in range(D)])

def rom1(dout, addr, clk):

    @instance
    def rdLogic() :
        while 1:
            yield clk.posedge
            dout.next = ROM[int(addr)]

    return rdLogic

def rom2(dout, addr, clk):
    
    theROM = ROM

    @instance
    def rdLogic() :
        while 1:
            yield clk.posedge
            dout.next = theROM[int(addr)]

    return rdLogic


def rom3(dout, addr, clk):


    @instance
    def rdLogic() :
        tmp = intbv(0)[8:]
        while 1:
            yield addr
            tmp[:] = ROM[int(addr)]
            dout.next = tmp

    return rdLogic


def rom4(dout, addr, clk):

    @always_comb
    def read():
        dout.next = ROM[int(addr)]

    return read

      

def RomBench(rom):

    dout = Signal(intbv(0)[8:])
    addr = Signal(intbv(1)[8:])
    clk = Signal(bool(0))

    rom_inst = rom(dout, addr, clk)

    @instance
    def stimulus():
        for i in range(D):
            addr.next = i
            yield clk.negedge
            yield clk.posedge
            yield delay(1)
            if __debug__:
                assert dout == ROM[i]
            print(dout)
        raise StopSimulation()

    @instance
    def clkgen():
        clk.next = 1
        while 1:
            yield delay(10)
            clk.next = not clk

    return clkgen, stimulus, rom_inst

def test1():
    assert conversion.verify(RomBench, rom1) == 0
    
def test2():
    assert conversion.verify(RomBench, rom2) == 0
    
def test3():
    assert conversion.verify(RomBench, rom3) == 0
    
def test4():
    assert conversion.verify(RomBench, rom4) == 0

        
        
    

