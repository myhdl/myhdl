from __future__ import generators

from random import randrange

from myhdl import Signal, Simulation, StopSimulation
from myhdl import intbv, delay, posedge, negedge, now, trace_sigs

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def Inc(count, enable, clock, reset, n):
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """
    while 1:
        yield posedge(clock), negedge(reset)
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n


def testbench():
    count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

    INC_1 = Inc(count, enable, clock, reset, n=4)

    def clockGen():
        while 1:
            yield delay(10)
            clock.next = not clock

    def stimulus():
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(12):
            enable.next = min(1, randrange(3))
            yield negedge(clock)
        raise StopSimulation

    def monitor():
        print "enable  count"
        yield posedge(reset)
        while 1:
            yield posedge(clock)
            yield delay(1)
            print "   %s      %s" % (enable, count)

    return clockGen(), stimulus(), INC_1, monitor()

tb = testbench()

def main():
    Simulation(tb).run()
    

if __name__ == '__main__':
    main()
           
           
    
        
    

    
             
        
