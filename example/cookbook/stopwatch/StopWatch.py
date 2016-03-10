import myhdl
from myhdl import *

from TimeCount import TimeCount
from bcd2led import bcd2led

def StopWatch(tens_led, ones_led, tenths_led, startstop, reset, clock):

    """ 3 digit stopwatch with seconds and tenths of a second.
    
    tens_led: 7 segment led for most significant digit of the seconds
    ones_led: 7 segment led for least significant digit of the seconds
    tenths_led: 7 segment led for tenths of a second
    startstop: input that starts or stops the stopwatch on a posedge
    reset: reset input
    clock: 10Hz clock input

    """

    tens, ones, tenths = [Signal(intbv(0)[4:]) for i in range(3)]

    timecount_inst = TimeCount(tens, ones, tenths, startstop, reset, clock)
    bcd2led_tens = bcd2led(tens_led, tens, clock)
    bcd2led_ones = bcd2led(ones_led, ones, clock)
    bcd2led_tenths = bcd2led(tenths_led, tenths, clock)

    return timecount_inst, bcd2led_tens, bcd2led_ones, bcd2led_tenths


def convert():
    
    tens_led, ones_led, tenths_led = [Signal(intbv(0)[7:]) for i in range(3)]
    startstop, reset, clock = [Signal(bool(0)) for i in range(3)]

    toVerilog(StopWatch, tens_led, ones_led, tenths_led, startstop, reset, clock)
    conversion.analyze(StopWatch, tens_led, ones_led, tenths_led, startstop, reset, clock)
                          

convert()
 
                        
                
                        
                
