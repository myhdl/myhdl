import unittest
from unittest import TestCase

import myhdl
from myhdl import *

from arith_utils import BEHAVIOR, STRUCTURE
from arith_utils import SLOW, FAST
from LeadZeroDet import LeadZeroDet

import random
random.seed = 1
from random import random

class LeadZeroDetTest(TestCase):

    """ Leading zeroes detector unit test class """

    def bench(self, width, speed, nrsamples=0):
        
        """ Leading zeroes detector test bench

        width -- decrementer bit width
        speed -- SLOW, MEDIUM or FAST
        nrsamples -- required number of random samples, or exhaustive
                     test if not set (default)
                     
        """

        A = Signal(intbv(0))
        ZS = Signal(intbv(0))
        ZB = Signal(intbv(0))

        beh = LeadZeroDet(width, speed, A, ZB, architecture=BEHAVIOR)
        str = LeadZeroDet(width, speed, A, ZS, architecture=STRUCTURE)

        @instance
        def stimulus():
            if nrsamples:
                vals = [long(random()*(2**width)) for i in range(nrsamples)]
            else:
                vals = range(2**width)
            for i in vals:
                A.next = intbv(i)
                yield delay(10)
                self.assertEqual(ZS, ZB)

        return (beh, str, stimulus)

    def testLeadZeroDetSmallSlow(self):
        Simulation(self.bench(width=8, speed=SLOW)).run()

    def testLeadZeroDetLargeSlow(self):
        Simulation(self.bench(width=39, speed=SLOW, nrsamples=16)).run()
        
    def testLeadZeroDetSmallFast(self):
        Simulation(self.bench(width=8, speed=FAST)).run()
        
    def testLeadZeroDetLargeFast(self):
        Simulation(self.bench(width=39, speed=FAST, nrsamples=16)).run()
         

if __name__ == "__main__":
    unittest.main()
       
                 




