import os
path = os.path
import unittest
from unittest import TestCase

from myhdl import *

def ram(dout, din, addr, we, clk, depth=128):
    """ Simple ram model """
  
    mem = [intbv(0)[8:] for i in range(depth)]
    while 1:
        yield posedge(clk)
        if we:
            mem[int(addr)][:] = din
        dout.next = mem[int(addr)]          
            
objfile = "mem.o"           
analyze_cmd = "iverilog -o %s mem_inst.v tb_mem_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
def ram_v(dout, din, addr, we, clk, depth=4):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestMemory(TestCase):

    def bench(self, depth=128):

        dout = Signal(intbv(0)[8:])
        dout_v = Signal(intbv(0)[8:])
        din = Signal(intbv(0)[8:])
        addr = Signal(intbv(0)[8:])
        we = Signal(bool())
        clk = Signal(bool())

        # mem_inst = ram(dout, din, addr, we, clk, depth)
        mem_inst = toVerilog(ram, dout, din, addr, we, clk, depth)
        mem_v_inst = ram_v(dout_v, din, addr, we, clk, depth)

        def stimulus():
            for i in range(depth):
                din.next = i
                addr.next = i
                we.next = True
                yield negedge(clk)
            we.next = False
            for i in range(depth):
                addr.next = i
                yield negedge(clk)
                yield posedge(clk)
                yield delay(1)
                self.assertEqual(dout, i)
                self.assertEqual(dout, dout_v)
            raise StopSimulation()

        def clkgen():
            while 1:
                yield delay(10)
                clk.next = not clk

        return clkgen(), stimulus(), mem_inst, mem_v_inst

    def test(self):
        sim = self.bench()
        Simulation(sim).run()

if __name__ == '__main__':
    unittest.main()
    

