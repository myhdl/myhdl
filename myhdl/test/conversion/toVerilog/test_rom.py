from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase
from random import randrange

from myhdl import *

from util import setupCosimulation

D = 256

ROM = tuple([randrange(D) for i in range(D)])
# ROM = [randrange(256) for i in range(256)]

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

      
def rom_v(name, dout, addr, clk):
    return setupCosimulation(**locals())

class TestRom(TestCase):

    def bench(self, rom):

        dout = Signal(intbv(0)[8:])
        dout_v = Signal(intbv(0)[8:])
        addr = Signal(intbv(1)[8:])
        clk = Signal(bool(0))

        # rom_inst = rom(dout, din, addr, we, clk, depth)
        rom_inst = toVerilog(rom, dout, addr, clk)
        rom_v_inst = rom_v(rom.__name__, dout_v, addr, clk)

        def stimulus():
            for i in range(D):
                addr.next = i
                yield clk.negedge
                yield clk.posedge
                yield delay(1)
                self.assertEqual(dout, ROM[i])
                self.assertEqual(dout, dout_v)
            raise StopSimulation()

        def clkgen():
            while 1:
                yield delay(10)
                clk.next = not clk

        return clkgen(), stimulus(), rom_inst, rom_v_inst

    def test1(self):
        sim = self.bench(rom1)
        Simulation(sim).run()
        
    def test2(self):
        sim = self.bench(rom2)
        Simulation(sim).run()
        
    def test3(self):
        sim = self.bench(rom3)
        Simulation(sim).run()
        
    def test4(self):
        sim = self.bench(rom4)
        Simulation(sim).run()
        
        

if __name__ == '__main__':
    unittest.main()
    

