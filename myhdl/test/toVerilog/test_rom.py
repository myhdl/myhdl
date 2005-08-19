import os
path = os.path
import unittest
from unittest import TestCase
from random import randrange

from myhdl import *

D = 256

ROM = tuple([randrange(D) for i in range(D)])
# ROM = [randrange(256) for i in range(256)]

def rom1(dout, addr, clk):

    def rdLogic() :
        while 1:
            yield posedge(clk)
            dout.next = ROM[int(addr)]

    RL = rdLogic()
    return RL

def rom2(dout, addr, clk):
    
    theROM = ROM
    
    def rdLogic() :
        while 1:
            yield posedge(clk)
            dout.next = theROM[int(addr)]

    RL = rdLogic()
    return RL


def rom3(dout, addr, clk):


    def rdLogic() :
        tmp = intbv(0)[8:]
        while 1:
            yield addr
            tmp[:] = ROM[int(addr)]
            dout.next = tmp

    RL = rdLogic()
    return RL


    
objfile = "rom.o"           
analyze_cmd = "iverilog -o %s rom_inst.v tb_rom_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
def rom_v(dout, addr, clk):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestRom(TestCase):

    def bench(self, rom):

        dout = Signal(intbv(0)[8:])
        dout_v = Signal(intbv(0)[8:])
        addr = Signal(intbv(1)[8:])
        clk = Signal(bool(0))

        # rom_inst = rom(dout, din, addr, we, clk, depth)
        rom_inst = toVerilog(rom, dout, addr, clk)
        rom_v_inst = rom_v(dout_v, addr, clk)

        def stimulus():
            for i in range(D):
                addr.next = i
                yield negedge(clk)
                yield posedge(clk)
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
        

if __name__ == '__main__':
    unittest.main()
    

