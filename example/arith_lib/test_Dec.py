from __future__ import generators
import unittest
from unittest import TestCase

from myhdl import Signal, intbv, delay, Simulation

from arith_utils import BEHAVIOR, STRUCTURE
from arith_utils import SLOW, FAST
from Dec import Dec

import random
random.seed = 1
from random import random

class DecTest(TestCase):

    def bench(self, width, speed, nrsamples=0):

        A = Signal(intbv())
        ZS = Signal(intbv())
        ZB = Signal(intbv())

        beh = Dec(width, speed, A, ZB, architecture=BEHAVIOR)
        str = Dec(width, speed, A, ZS, architecture=STRUCTURE)

        def stimulus():
            if nrsamples:
                vals = [long(random()*(2**width)) for i in range(nrsamples)]
            else:
                vals = range(2**width)
            for i in vals:
                A.next = intbv(i)
                yield delay(10)
                # print "a:%s Res: %s %s" % (A.val, ZS.val, ZB.val)
                self.assertEqual(ZS.val, ZB.val)

        return (beh, str, stimulus())

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
       
                 




