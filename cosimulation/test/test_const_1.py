import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import Simulation, StopSimulation, Signal, \
                  delay, intbv, negedge, posedge, now

from const_1 import const_1

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

class TestConst(TestCase):

    vals = [randrange(2) for i in range(1000)]

    def clkGen(self, clk):
        while 1:
            yield delay(10)
            clk.next = not clk


    def stimulus(self, clk):
        for v in self.vals:
            yield negedge(clk)
        raise StopSimulation


    def check(self, q, clk):
        for v in self.vals:
            yield posedge(clk)
        self.assertEqual(q, 1)


    def bench(self):

        # Note: when this is initialized different (ie: 0) than the constant value of q (1)
        # the cosimulation never updates the signal q and the assertion in check fails
        q, clk = [Signal(intbv(0)) for i in range(2)]

        CONST_1 = const_1(q, clk)
        CLK_1 = self.clkGen(clk)
        ST_1 = self.stimulus(clk)
        CH_1 = self.check(q, clk)

        sim = Simulation(CONST_1, CLK_1, ST_1, CH_1)
        return sim


    def test1(self):
        """ const test """
        sim = self.bench()
        sim.run(quiet=1)


    def test2(self):
        """ const test with simulation suspends """
        sim = self.bench()
        while sim.run(duration=randrange(1,5), quiet=1):
            pass


if __name__ == '__main__':
    unittest.main()















