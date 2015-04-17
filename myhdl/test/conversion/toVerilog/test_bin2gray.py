from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase

from myhdl import *

from util import setupCosimulation

def bin2gray2(B, G, width):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """
    @instance
    def logic():
        Bext = intbv(0)[width+1:]
        while 1:
            yield B
            Bext[:] = B
            for i in range(width):
                G.next[i] = Bext[i+1] ^ Bext[i]
    return logic

def bin2gray(B, G, width):
    
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    
    """

    @always_comb
    def logic():
        Bext = intbv(0)[width+1:]
        Bext[:] = B
        for i in range(width):
            G.next[i] = Bext[i+1] ^ Bext[i]

    return logic
           
            
objfile = "bin2gray.o"           
analyze_cmd = "iverilog -o %s bin2gray_inst.v tb_bin2gray_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
      
 
def bin2gray_v(B, G):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

def bin2gray_v(name, B, G):
    return setupCosimulation(**locals())


class TestBin2Gray(TestCase):

    def bench(self, width, bin2gray):

        B = Signal(intbv(0)[width:])
        G = Signal(intbv(0)[width:])
        G_v = Signal(intbv(0)[width:])

        bin2gray_inst = toVerilog(bin2gray, B, G, width)
        # bin2gray_inst = bin2gray(B, G, width)
        bin2gray_v_inst = bin2gray_v(bin2gray.__name__, B, G_v)

        def stimulus():
            for i in range(2**width):
                B.next = intbv(i)
                yield delay(10)
                #print "B: " + bin(B, width) + "| G_v: " + bin(G_v, width)
                #print bin(G, width)
                #print bin(G_v, width)
                self.assertEqual(G, G_v)

        return bin2gray_v_inst, stimulus(), bin2gray_inst

    def test1(self):
        sim = self.bench(width=8, bin2gray=bin2gray)
        Simulation(sim).run()
        
    def test2(self):
        sim = self.bench(width=8, bin2gray=bin2gray2)
        Simulation(sim).run()
    

if __name__ == '__main__':
    unittest.main()
    

