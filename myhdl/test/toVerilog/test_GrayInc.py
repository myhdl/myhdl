import os
path = os.path
import unittest
from random import randrange

from myhdl import *

from test_bin2gray import bin2gray
from test_inc import incRef as inc

from util import setupCosimulation

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def GrayInc(graycnt, enable, clock, reset, width):
    
    bincnt = Signal(intbv()[width:])
    
    INC_1 = inc(bincnt, enable, clock, reset, n=2**width)
    BIN2GRAY_1 = bin2gray(B=bincnt, G=graycnt, width=width)
    
    return INC_1, BIN2GRAY_1


def GrayIncReg(graycnt, enable, clock, reset, width):
    
    graycnt_comb = Signal(intbv()[width:])
    
    GRAY_INC_1 = GrayInc(graycnt_comb, enable, clock, reset, width)
    
    def reg():
        while 1:
            yield posedge(clock)
            graycnt.next = graycnt_comb
    REG_1 = reg()
    
    return GRAY_INC_1, REG_1


width = 8
graycnt = Signal(intbv()[width:])
enable, clock, reset = [Signal(bool()) for i in range(3)]
# GrayIncReg(graycnt, enable, clock, reset, width)

def GrayIncReg_v(name, graycnt, enable, clock, reset, width):
    return setupCosimulation(**locals())

graycnt_v = Signal(intbv()[width:])

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
            yield negedge(clock)
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield negedge(clock)
        raise StopSimulation

    def check(self):
        expect = 0
        yield posedge(reset)
        self.assertEqual(graycnt, graycnt_v)
        while 1:
            yield posedge(clock)
            if enable:
                expect = (expect + 1) % (2 ** width)
            yield delay(1)
            # print "%d graycnt %s %s" % (now(), graycnt, graycnt_v)
            self.assertEqual(graycnt, graycnt_v)
                
    def bench(self):
        GRAY_INC_REG_1 = toVerilog(GrayIncReg, graycnt, enable, clock, reset, width)
        GRAY_INC_REG_v = GrayIncReg_v(GrayIncReg.func_name, graycnt_v, enable, clock, reset, width)
        clk_1 = self.clockGen()
        st_1 = self.stimulus()
        ch_1 = self.check()
        sim = Simulation(GRAY_INC_REG_1, GRAY_INC_REG_v, clk_1, st_1, ch_1)
        return sim

    def test(self):
        """ Check gray inc operation """
        sim = self.bench()
        sim.run(quiet=1)
        

          
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        


  
