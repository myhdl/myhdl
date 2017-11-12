from __future__ import generators

import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

#import psyco
#psyco.profile()

from myhdl import Simulation, StopSimulation, Signal, \
                  delay, intbv, negedge, posedge, now

from inc import inc

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

class TestInc(TestCase):

    def clockGen(self, clock):
        while 1:
            yield delay(10)
            clock.next = not clock
    
    def stimulus(self, enable, clock, reset):
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield negedge(clock)
        raise StopSimulation

    def check(self, count, enable, clock, reset, n):
        expect = 0
        yield posedge(reset)
        self.assertEqual(count, expect)
        while 1:
            yield posedge(clock)
            if enable:
                expect = (expect + 1) % n
            yield delay(1)
            # print "%d count %s expect %s" % (now(), count, expect)
            self.assertEqual(count, expect)
                
    def bench(self):

        n = 253

        count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

        INC_1 = inc(count, enable, clock, reset, n=n)
        CLK_1 = self.clockGen(clock)
        ST_1 = self.stimulus(enable, clock, reset)
        CH_1 = self.check(count, enable, clock, reset, n=n)

        sim = Simulation(INC_1, CLK_1, ST_1, CH_1)
        return sim

    def test1(self):
        """ Check increment operation """
        sim = self.bench()
        sim.run(quiet=1)
        
    def test2(self):
        """ Check increment operation with suspended simulation runs """
        sim = self.bench()
        while sim.run(duration=randrange(1, 6), quiet=1):
            pass

          
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

