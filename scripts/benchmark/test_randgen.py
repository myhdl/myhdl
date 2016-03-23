from __future__ import absolute_import
import myhdl
from myhdl import *

from random_generator import random_generator

def test_randgen():

    random_word = Signal(intbv(0)[31:])
    enable = Signal(bool())
    clock = Signal(bool())
    reset = Signal(bool())
    
    dut = random_generator(random_word, enable, clock, reset)

    @instance
    def stimulus():
        enable.next = 0
        clock.next = 0
        reset.next = 0
        yield delay(10)
        reset.next = 1
        yield delay(10)
        reset.next = 0
        enable.next = 1
        for i in range(2**20):
            yield delay(10)
            clock.next = 1
            yield delay(10)
            clock.next = 0
            print random_word
        
    return dut, stimulus

if __name__ == '__main__':
    tb = Simulation(test_randgen())
    tb.run()

