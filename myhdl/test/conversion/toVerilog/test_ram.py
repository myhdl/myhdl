from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase

from myhdl import *

from util import setupCosimulation

def ram(dout, din, addr, we, clk, depth=128):
    """ Simple ram model """
  
    @instance
    def logic():
        mem = [intbv(0)[8:] for i in range(depth)]
        a = intbv(0)[8:]
        # ad = 1
        while 1:
            yield clk.posedge
            if we:
                ad = int(addr)
                mem[int(addr)][:] = din
                # a = din.val
                # a[2] = din
            dout.next = mem[int(addr)]

    return logic
        

def ram_clocked(dout, din, addr, we, clk, depth=128):
    """ Ram model """
    
    mem = [Signal(intbv(0)[8:]) for i in range(depth)]

    @instance
    def access():
        while 1:
            yield clk.posedge
            if we:
                mem[int(addr)].next = din
            dout.next = mem[int(addr)]
            
    return access

def ram_deco1(dout, din, addr, we, clk, depth=128):
    """  Ram model """
    
    mem = [Signal(intbv(0)[8:]) for i in range(depth)]

    @instance
    def write():
        while 1:
            yield clk.posedge
            if we:
                mem[int(addr)].next = din
                
    @always_comb
    def read():
        dout.next = mem[int(addr)]
        
    return write, read

def ram_deco2(dout, din, addr, we, clk, depth=128):
    """  Ram model """
    
    mem = [Signal(intbv(0)[8:]) for i in range(depth)]

    @always(clk.posedge)
    def write():
        if we:
            mem[int(addr)].next = din
                
    @always_comb
    def read():
        dout.next = mem[int(addr)]

    return write, read



def ram2(dout, din, addr, we, clk, depth=128):
        
    # memL = [intbv(0,min=dout._min,max=dout._max) for i in range(depth)]
    memL = [Signal(intbv()[len(dout):]) for i in range(depth)]

    @instance
    def wrLogic() :
        while 1:
            yield clk.posedge
            if we:
                memL[int(addr)].next = din

    @instance
    def rdLogic() :
        while 1:
            yield clk.posedge
            dout.next = memL[int(addr)]

    return wrLogic, rdLogic

  
def ram_v(name, dout, din, addr, we, clk, depth=4):
    return setupCosimulation(**locals())

class TestMemory(TestCase):

    def bench(self, ram, depth=128):

        dout = Signal(intbv(0)[8:])
        dout_v = Signal(intbv(0)[8:])
        din = Signal(intbv(0)[8:])
        addr = Signal(intbv(0)[7:])
        we = Signal(bool(0))
        clk = Signal(bool(0))

        # mem_inst = ram(dout, din, addr, we, clk, depth)
        mem_inst = toVerilog(ram, dout, din, addr, we, clk, depth)
        mem_v_inst = ram_v(ram.__name__, dout_v, din, addr, we, clk, depth)

        def stimulus():
            for i in range(depth):
                din.next = i
                addr.next = i
                we.next = True
                yield clk.negedge
            we.next = False
            for i in range(depth):
                addr.next = i
                yield clk.negedge
                yield clk.posedge
                yield delay(1)
                #print dout
                #print dout_v
                self.assertEqual(dout, i)
                # self.assertEqual(dout, dout_v)
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
        
    def testram_clocked(self):
        sim = self.bench(ram_clocked)
        Simulation(sim).run()
        
    def testram_deco1(self):
        sim = self.bench(ram_deco1)
        Simulation(sim).run()
        
    def testram_deco2(self):
        sim = self.bench(ram_deco2)
        Simulation(sim).run()
        

if __name__ == '__main__':
    unittest.main()
    

