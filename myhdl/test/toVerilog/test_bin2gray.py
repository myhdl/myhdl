import os
path = os.path
import unittest
from unittest import TestCase

from myhdl import *

def bin2gray(B, G, width):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """
    while 1:
        yield B
        for i in range(width):
            G.next[i] = B[i] ^ B[i]
            
analyze_cmd = "iverilog -o bin2gray bin2gray_1.v tb_bin2gray_1.v"
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi bin2gray"
      
 
def bin2gray_v(B, G):
    if path.exists("bin2gray"):
        os.remove("bin2gray")
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestBin2Gray(TestCase):

    def bench(self, width):

        B = Signal(intbv(0)[9:])
        G = Signal(intbv(0)[8:])
        G_v = Signal(intbv(0)[8:])

        bin2gray_1 = toVerilog(bin2gray, B, G, width)
        bin2gray_2 = bin2gray_v(B, G_v)

        def stimulus():
            for i in range(2**width):
                B.next = intbv(i)
                yield delay(10)
                #print "B: " + bin(B, width) + "| G_v: " + bin(G_v, width)
                #print bin(G, width)
                #print bin(G_v, width)
                self.assertEqual(G, G_v)

        return bin2gray_2, stimulus(), bin2gray_1

    def test(self):
        sim = self.bench(width=8)
        Simulation(sim).run()
    

if __name__ == '__main__':
    unittest.main()
    

