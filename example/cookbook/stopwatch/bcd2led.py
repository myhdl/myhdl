import seven_segment

import myhdl
from myhdl import *

code = [None] * 10
for key, val in seven_segment.encoding.items():
    if 0 <= key <= 9:
        code[key] = int(val, 2)
code = tuple(code)

def bcd2led(led, bcd, clock):

    """ bcd to seven segment led convertor.

    led: seven segment led output
    bcd: bcd input
    clock: clock input

    """

    @always(clock.posedge)
    def logic():
        led.next = code[int(bcd)]

    return logic


def convert():
    led = Signal(intbv(0)[7:])
    bcd = Signal(intbv(0)[4:])
    clock = Signal(False)
    toVerilog(bcd2led, led, bcd, clock)
    toVHDL(bcd2led, led, bcd, clock)


convert()
