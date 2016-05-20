import unittest

from myhdl import Simulation, Signal, delay, intbv, bin

from bin2gray import bin2gray

MAX_WIDTH = 11

class TestGrayCodeProperties(unittest.TestCase):

    def testSingleBitChange(self):
        """Check that only one bit changes in successive codewords."""

        def test(B, G):
            w = len(B)
            G_Z = Signal(intbv(0)[w:])
            B.next = intbv(0)
            yield delay(10)
            for i in range(1, 2**w):
                G_Z.next = G
                B.next = intbv(i)
                yield delay(10)
                diffcode = bin(G ^ G_Z)
                self.assertEqual(diffcode.count('1'), 1)

        self.runTests(test)

    def testUniqueCodeWords(self):
        """Check that all codewords occur exactly once."""

        def test(B, G):
            w = len(B)
            actual = []
            for i in range(2**w):
                B.next = intbv(i)
                yield delay(10)
                actual.append(int(G))
            actual.sort()
            expected = list(range(2**w))
            self.assertEqual(actual, expected)

        self.runTests(test)


    def runTests(self, test):
        """Helper method to run the actual tests."""
        for w in range(1, MAX_WIDTH):
            B = Signal(intbv(0)[w:])
            G = Signal(intbv(0)[w:])
            dut = bin2gray(B, G)
            check = test(B, G)
            sim = Simulation(dut, check)
            sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
