from __future__ import generators

import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import Simulation, StopSimulation, Signal, \
                  delay, intbv, negedge, posedge, now

from dff import dff

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

class TestDff(TestCase):

    def bench(self):
        
        """ Check D flip-flop operation """

        q, d, clock, reset = [Signal(intbv(0)) for i in range(4)]

        DFF_1 = dff(q, d, clock, reset)

        vals = [randrange(2) for i in range(1000)]
        
        def clockGen():
            while 1:
                yield delay(10)
                clock.next = not clock
        
        def stimulus():
            reset.next = ACTIVE_LOW
            yield negedge(clock)
            reset.next = INACTIVE_HIGH
            for v in vals:
                d.next = v
                yield negedge(clock)
            raise StopSimulation
            
        def check():
            yield posedge(reset)
            for v in vals:
                yield posedge(clock)
                yield delay(1)
                self.assertEqual(q, v)

        sim = Simulation(clockGen(), stimulus(), DFF_1, check())
        return sim

    def test1(self):
        """ Basic dff test """
        sim = self.bench()
        sim.run(quiet=1)
        
    def test2(self):
        """ dff test with simulation suspends """
        sim = self.bench()
        while sim.run(duration=randrange(1,5), quiet=1):
            pass

if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

