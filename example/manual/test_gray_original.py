import unittest

from myhdl import Simulation, Signal, delay, intbv, bin

from bin2gray import bin2gray
from next_gray_code import nextLn

MAX_WIDTH = 11

class TestOriginalGrayCode(unittest.TestCase):

    def testOriginalGrayCode(self):
        """Check that the code is an original Gray code."""

        Rn = []

        def stimulus(B, G, n):
            for i in range(2**n):
                B.next = intbv(i)
                yield delay(10)
                Rn.append(bin(G, width=n))

        Ln = ['0', '1'] # n == 1
        for w in range(2, MAX_WIDTH):
            Ln = nextLn(Ln)
            del Rn[:]
            B = Signal(intbv(0)[w:])
            G = Signal(intbv(0)[w:])
            dut = bin2gray(B, G)
            stim = stimulus(B, G, w)
            sim = Simulation(dut, stim)
            sim.run(quiet=1)
            self.assertEqual(Ln, Rn)


if __name__ == '__main__':
    unittest.main(verbosity=2)
