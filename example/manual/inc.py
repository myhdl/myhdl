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
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(12):
            enable.next = min(1, randrange(3))
            yield clock.negedge
        raise StopSimulation

    @instance
    def monitor():
        print "enable  count"
        yield reset.posedge
        while 1:
            yield clock.posedge
            yield delay(1)
            print "   %s      %s" % (enable, count)

    return clockGen, stimulus, inc_1, monitor

tb = testbench()

def main():
    Simulation(tb).run()


# conversion
m = 8
n = 2 ** m

count = Signal(intbv(0)[m:])
enable = Signal(bool(0))
clock, reset = [Signal(bool()) for i in range(2)]

inc_inst = Inc(count, enable, clock, reset, n=n)
inc_inst = toVerilog(Inc, count, enable, clock, reset, n=n)
inc_inst = toVHDL(Inc, count, enable, clock, reset, n=n)


if __name__ == '__main__':
    main()
           
           
    
        
    

    
             
        
