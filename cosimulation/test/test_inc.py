from __future__ import generators

import unittest
from unittest import TestCase
from random import randrange

from myhdl import Simulation, StopSimulation, Signal, \
                  delay, intbv, negedge, posedge

from inc import inc

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

class TestInc(TestCase):

    def testInc(self):
        
        """ Check increment operation """

        n = 253

        count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

        INC_1 = inc(count, enable, clock, reset, n=n)
        
        def clockGen():
            while 1:
                yield delay(10)
                clock.next = not clock
        
        def stimulus():
            reset.next = ACTIVE_LOW
            yield negedge(clock)
            reset.next = INACTIVE_HIGH
            for i in range(1000):
                enable.next = min(1, randrange(7))
                yield negedge(clock)
            raise StopSimulation
            
        def check():
            expect = 0
            yield posedge(reset)
            self.assertEqual(count, expect)
            while 1:
                yield posedge(clock)
                if enable:
                    expect = (count + 1) % n
                yield delay(1)
                print "count %s expect %s" % (count, expect)
                # self.assertEqual(count, expect)

        Simulation(clockGen(), stimulus(), INC_1, check()).run(quiet=1)        

          
if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

