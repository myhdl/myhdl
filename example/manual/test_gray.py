from __future__ import generators

import unittest
from unittest import TestCase

from myhdl import Simulation, Signal, delay, intbv, bin

from bin2gray import bin2gray

MAX_WIDTH = 10

def nextLn(Ln):
    """ Return Gray code Ln+1, given Ln. """
    Ln0 = ['0' + codeword for codeword in Ln]
    Ln1 = ['1' + codeword for codeword in Ln]
    Ln1.reverse()
    return Ln0 + Ln1

## def bin2gray(B, G, width):
##     while 1:
##         yield B
##         G.next = B[0]

class TestOriginalGrayCode(TestCase):

    def testOriginalGrayCode(self):
        
        """ Check that the code is an original Gray code """

        B = Signal(intbv(-1))
        G = Signal(intbv(0))
        Rn = []
        
        def stimulus(n):
            for i in range(2**n):
                B.next = intbv(i)
                yield delay(10)
                Rn.append(bin(G, width=n))
        
        Ln = ['0', '1'] # n == 1
        for n in range(2, MAX_WIDTH):
            Ln = nextLn(Ln)
            del Rn[:]
            dut = bin2gray(B, G, n)
            sim = Simulation(dut, stimulus(n))
            sim.run(quiet=1)
            self.assertEqual(Ln, Rn)


class TestGrayCodeProperties(TestCase):

    def testSingleBitChange(self):
        
        """ Check that only one bit changes in successive codewords """

        B = Signal(intbv(-1))
        G = Signal(intbv(0))
        G_Z = Signal(intbv(0))
        
        def test(width):
            B.next = intbv(0)
            yield delay(10)
            for i in range(1, 2**width):
                G_Z.next = G
                B.next = intbv(i)
                yield delay(10)
                diffcode = bin(G ^ G_Z)
                self.assertEqual(diffcode.count('1'), 1)
        
        for width in range(MAX_WIDTH):
            dut = bin2gray(B, G, width)
            sim = Simulation(dut, test(width))
            sim.run(quiet=1)


    def testUniqueCodeWords(self):
        
        """ Check that all codewords occur exactly once """

        B = Signal(intbv(-1))
        G = Signal(intbv(0))

        def test(width):
            actual = []
            for i in range(2**width):
                B.next = intbv(i)
                yield delay(10)
                actual.append(int(G))
            actual.sort()
            expected = range(2**width)
            self.assertEqual(actual, expected)
       
        for width in range(MAX_WIDTH):
            dut = bin2gray(B, G, width)
            sim = Simulation(dut, test(width))
            sim.run(quiet=1)
            

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

