from __future__ import absolute_import
import os
path = os.path
import unittest
from random import randrange

from myhdl import *

from test_bin2gray import bin2gray
from test_inc import inc

from util import setupCosimulation

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def GrayInc(graycnt, enable, clock, reset, width):
    
    bincnt = Signal(intbv(0)[width:])
    
    inc_1 = inc(bincnt, enable, clock, reset, n=2**width)
    bin2gray_1 = bin2gray(B=bincnt, G=graycnt, width=width)
    
    return inc_1, bin2gray_1


def GrayIncReg(graycnt, enable, clock, reset, width):
    
    graycnt_comb = Signal(intbv(0)[width:])
    
    gray_inc_1 = GrayInc(graycnt_comb, enable, clock, reset, width)

    @always(clock.posedge)
    def reg_1():
        graycnt.next = graycnt_comb
    
    return gray_inc_1, reg_1


width = 8
graycnt = Signal(intbv(0)[width:])
enable, clock, reset = [Signal(bool()) for i in range(3)]
# GrayIncReg(graycnt, enable, clock, reset, width)

def GrayIncReg_v(name, graycnt, enable, clock, reset, width):
    return setupCosimulation(**locals())

graycnt_v = Signal(intbv(0)[width:])

class TestGrayInc(unittest.TestCase):

    def clockGen(self):
        while 1:
            yield delay(10)
            clock.next = not clock

    def stimulus(self):
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = 1
            yield clock.negedge
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield clock.negedge
        raise StopSimulation

    def check(self):
        yield reset.posedge
        self.assertEqual(graycnt, graycnt_v)
        while 1:
            yield clock.posedge
            yield delay(1)
            # print "%d graycnt %s %s" % (now(), graycnt, graycnt_v)
            self.assertEqual(graycnt, graycnt_v)
                
    def bench(self):
        gray_inc_reg_1 = toVerilog(GrayIncReg, graycnt, enable, clock, reset, width)
        gray_inc_reg_v = GrayIncReg_v(GrayIncReg.__name__, graycnt_v, enable, clock, reset, width)
        clk_1 = self.clockGen()
        st_1 = self.stimulus()
        ch_1 = self.check()
        sim = Simulation(gray_inc_reg_1, gray_inc_reg_v, clk_1, st_1, ch_1)
        return sim

    def test(self):
        """ Check gray inc operation """
        sim = self.bench()
        sim.run(quiet=1)
        

          
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        


  
