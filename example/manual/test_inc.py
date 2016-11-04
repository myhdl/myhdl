import random
from myhdl import block, always, instance, Signal, \
    ResetSignal, modbv, delay, StopSimulation
from inc import inc

random.seed(1)
randrange = random.randrange

ACTIVE_LOW, INACTIVE_HIGH = 0, 1

@block
def testbench():
    m = 3
    count = Signal(modbv(0)[m:])
    enable = Signal(bool(0))
    clock  = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)

    inc_1 = inc(count, enable, clock, reset)

    HALF_PERIOD = delay(10)

    @always(HALF_PERIOD)
    def clockGen():
        clock.next = not clock

    @instance
    def stimulus():
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(16):
            enable.next = min(1, randrange(3))
            yield clock.negedge
        raise StopSimulation()

    @instance
    def monitor():
        print("enable  count")
        yield reset.posedge
        while 1:
            yield clock.posedge
            yield delay(1)
            print("   %s      %s" % (int(enable), count))

    return clockGen, stimulus, inc_1, monitor

tb = testbench()
tb.run_sim()
