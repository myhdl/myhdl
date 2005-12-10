from random import randrange
from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def Inc(count, enable, clock, reset, n):
    
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    
    """
    
    @always(clock.posedge, reset.negedge)
    def incLogic():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n

    return incLogic


def testbench():
    count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

    inc_1 = Inc(count, enable, clock, reset, n=4)

    HALF_PERIOD = delay(10)

    @always(HALF_PERIOD)
    def clockGen():
        clock.next = not clock

    @instance
    def stimulus():
        reset.next = ACTIVE_LOW
        yield negedge(clock)
        reset.next = INACTIVE_HIGH
        for i in range(12):
            enable.next = min(1, randrange(3))
            yield negedge(clock)
        raise StopSimulation

    @instance
    def monitor():
        print "enable  count"
        yield posedge(reset)
        while 1:
            yield posedge(clock)
            yield delay(1)
            print "   %s      %s" % (enable, count)

    return clockGen, stimulus, inc_1, monitor

tb = testbench()

def main():
    Simulation(tb).run()
    

if __name__ == '__main__':
    main()
           
           
    
        
    

    
             
        
