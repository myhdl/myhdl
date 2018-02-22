import unittest
from unittest import TestCase

import myhdl
from myhdl import *

from arith_utils import BEHAVIOR, STRUCTURE
from arith_utils import SLOW, FAST
from Dec import Dec

import random
random.seed = 1
from random import random

class DecTest(TestCase):

    """ Decrementer unit test class """

    def bench(self, width, speed, nrsamples=0):
        
        """ Decrementer test bench

        width -- decrementer bit width
        speed -- SLOW, MEDIUM or FAST
        nrsamples -- required number of random samples, or exhaustive
                     test if not set (default)
                     
        """

        A = Signal(intbv(0))
        ZS = Signal(intbv(0))
        ZB = Signal(intbv(0))

        beh = Dec(width, speed, A, ZB, architecture=BEHAVIOR)
        str = Dec(width, speed, A, ZS, architecture=STRUCTURE)

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

    def testDecSmallSlow(self):
        Simulation(self.bench(width=8, speed=SLOW)).run()

    def testDecLargeSlow(self):
        Simulation(self.bench(width=39, speed=SLOW, nrsamples=16)).run()
        
    def testDecSmallFast(self):
        Simulation(self.bench(width=8, speed=FAST)).run()
        
    def testDecLargeFast(self):
        Simulation(self.bench(width=39, speed=FAST, nrsamples=16)).run()
         

if __name__ == "__main__":
    unittest.main()
       
                 




