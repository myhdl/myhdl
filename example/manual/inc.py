from random import randrange
from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

def Inc(count, enable, clock, reset):
    
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    
    """
    
    @always_seq(clock.posedge, reset=reset)
    def incLogic():
        if enable:
            count.next = count + 1

    return incLogic


def testbench():
    m = 3
    count = Signal(modbv(0)[m:])
    enable = Signal(bool(0))
    clock  = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)

    inc_1 = Inc(count, enable, clock, reset)

    HALF_PERIOD = delay(10)

    @always(HALF_PERIOD)
    def clockGen():
        clock.next = not clock

    @instance
    def stimulus():
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(20):
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

count = Signal(modbv(0)[m:])
enable = Signal(bool(0))
clock  = Signal(bool(0))
reset = ResetSignal(0, active=0, async=True)

inc_inst = Inc(count, enable, clock, reset)
inc_inst = toVerilog(Inc, count, enable, clock, reset)
inc_inst = toVHDL(Inc, count, enable, clock, reset)


if __name__ == '__main__':
    main()
           
           
    
        
    

    
             
        
