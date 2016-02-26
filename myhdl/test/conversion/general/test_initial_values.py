from __future__ import absolute_import
from random import randrange

from myhdl import *

def initial_value_bench(initial_val, change_input_signal):

    clk = Signal(bool(0))

    input_signal = Signal(initial_val)
    
    if change_input_signal:
        # Make sure it doesn't overflow when changing
        if initial_val > 0:
            input_signal.val[:] = initial_val - 1
        else:
            input_signal.val[:] = initial_val + 1

    if isinstance(initial_val, bool):
        output_signal = Signal(not initial_val)
        update_val = not initial_val
    else:
        output_signal = Signal(
            intbv(0, min=initial_val.min, max=initial_val.max))
        update_val = 0

    expected_output = input_signal._init

    N = 10
    first = [True]

    @instance
    def clkgen():
        clk.next = 1

        for n in range(N):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()
            
    @always_comb
    def output_driver():
        output_signal.next = input_signal

    @always(clk)
    def compare_output():

        input_signal.next = update_val

        if __debug__:
            if first[0]:
                assert output_signal == expected_output
                first[0] = False
            else:
                assert output_signal == update_val

        print(int(output_signal))

    return clkgen, output_driver, compare_output

def runner(initial_val, change_input_signal=False):
    pre_toVerilog_no_initial_value = toVerilog.no_initial_value
    pre_toVHDL_no_initial_value = toVerilog.no_initial_value

    toVerilog.no_initial_value = False
    toVHDL.no_initial_value = False

    assert conversion.verify(
        initial_value_bench, initial_val, change_input_signal) == 0
    
    toVerilog.no_initial_value = pre_toVerilog_no_initial_value
    toVHDL.no_initial_value = pre_toVHDL_no_initial_value

def test_unsigned():
    '''The correct initial value should be used for unsigned type signal.
    '''
    min_val = 0
    max_val = 34
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val)


def test_signed():
    '''The correct initial value should be used for signed type signal.
    '''
    min_val = -12
    max_val = 4
    
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val)

def test_long_signals():
    '''The correct initial value should work with wide bitwidths.
    '''
    min_val = -(2**71)
    max_val = 2**71 - 1
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val)

def test_bool_signals():
    '''The correct initial value should be used for a boolean type signal
    '''
    initial_val = True

    runner(initial_val)

def test_init_user():
    '''It should be the _init attribute that is used for initialisation

    It should not be the current value, which should be ignored.
    '''
    min_val = -34
    max_val = 15
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val, change_input_signal=True)

