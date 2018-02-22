from __future__ import absolute_import
import myhdl
from myhdl import *

from lfsr24 import lfsr24

def test_lfsr24():

    lfsr = Signal(modbv(0)[24:])
    enable = Signal(bool())
    clock = Signal(bool())
    reset = Signal(bool())
    
    dut = lfsr24(lfsr, enable, clock, reset)

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
        for i in range(2**24 - 2):
            yield delay(10)
            clock.next = 1
            yield delay(10)
            clock.next = 0
            assert lfsr != 1
        yield delay(10)
        clock.next = 1
        yield delay(10)
        assert lfsr == 1 
        
    return dut, stimulus

if __name__ == '__main__':
    tb = Simulation(test_lfsr24())
    tb.run()

       
