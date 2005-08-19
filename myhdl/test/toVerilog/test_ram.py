import os
path = os.path
import unittest
from unittest import TestCase

from myhdl import *

def ram(dout, din, addr, we, clk, depth=128):
    """ Simple ram model """
  
    mem = [intbv(0)[8:] for i in range(depth)]
    a = intbv(0)[8:]
    # ad = 1
    while 1:
        yield posedge(clk)
        if we:
            ad = int(addr)
            mem[int(addr)][:] = din
            # a = din.val
            # a[2] = din
        dout.next = mem[int(addr)]


def ram2(dout, din, addr, we, clk, depth=128):
        
    # memL = [intbv(0,min=dout._min,max=dout._max) for i in range(depth)]
    memL = [Signal(intbv()[len(dout):]) for i in range(depth)]
    def wrLogic() :
        while 1:
            yield posedge(clk)
            if we:
                memL[int(addr)].next = din

    def rdLogic() :
        while 1:
            yield posedge(clk)
            dout.next = memL[int(addr)]

    WL = wrLogic()
    RL = rdLogic()
    return WL,RL

def ram3(dout, din, addr, we, clk, depth=128):
        
    memL = [Signal(intbv(0)[len(dout):]) for i in range(depth)]
    read_addr = Signal(intbv(0)[len(addr):])
    # mem = memL[:]
    # p = memL[3]
    
    def wrLogic() :
        while 1:
            yield posedge(clk)
            if we:
                memL[int(addr)].next = din
            read_addr.next = addr
    WL = wrLogic()
            
    def rdLogic() :
        dout.next = memL[int(read_addr)]
    RL = always_comb(rdLogic)
    
    return WL,RL


            
objfile = "mem.o"           
analyze_cmd = "iverilog -o %s mem_inst.v tb_mem_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
def ram_v(dout, din, addr, we, clk, depth=4):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestMemory(TestCase):

    def bench(self, ram, depth=128):

        dout = Signal(intbv(0)[8:])
        dout_v = Signal(intbv(0)[8:])
        din = Signal(intbv(0)[8:])
        addr = Signal(intbv(0)[8:])
        we = Signal(bool(0))
        clk = Signal(bool(0))

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
                #print dout
                #print dout_v
                self.assertEqual(dout, i)
                self.assertEqual(dout, dout_v)
            raise StopSimulation()

        def clkgen():
            while 1:
                yield delay(10)
                clk.next = not clk

        return clkgen(), stimulus(), mem_inst, mem_v_inst

    def test1(self):
        sim = self.bench(ram)
        Simulation(sim).run()
        
    def test2(self):
        sim = self.bench(ram2)
        Simulation(sim).run()
        
    def test3(self):
        sim = self.bench(ram3)
        Simulation(sim).run()

if __name__ == '__main__':
    unittest.main()
    

