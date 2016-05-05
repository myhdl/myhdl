from __future__ import absolute_import
from random import randrange

from myhdl import *
import myhdl

@block
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

        clk.next = 0
        for n in range(N):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()
            
    @always_comb
    def output_driver():
        output_signal.next = input_signal

    @always(clk.posedge)
    def drive_and_check():

        input_signal.next = update_val

        if __debug__:
            if first[0]:
                assert output_signal == expected_output
                first[0] = False
            else:
                assert output_signal == update_val

    @always(clk.posedge)
    def output_writer():
        print(output_signal)

    return clkgen, output_driver, drive_and_check, output_writer

@block
def canonical_list_writer(output_signal_list, clk):

    signal_list_length = len(output_signal_list)

    @always(clk.posedge)
    def list_writer():
        for i in range(signal_list_length):
            print(str(output_signal_list[i]._val))
            
    canonical_list_writer.verilog_code = '''
always @(posedge $clk) begin: INITIAL_VALUE_LIST_BENCH_CANONICAL_LIST_WRITER_0_LIST_WRITER
    integer i;
    for (i=0; i<10; i=i+1) begin
        $$write("%h", output_signal_list[i]);
        $$write("\\n");
    end
end
'''
    canonical_list_writer.vhdl_code = '''
INITIAL_VALUE_BENCH_OUTPUT_WRITER: process ($clk) is
    variable L: line;
begin
    if rising_edge($clk) then
        for i in 0 to $signal_list_length-1 loop
            write(L, to_hstring(unsigned(output_signal_list(i))));
            writeline(output, L);
        end loop;
    end if;
end process INITIAL_VALUE_BENCH_OUTPUT_WRITER;
'''
    return list_writer


@block
def initial_value_list_bench(initial_vals, change_input_signal):
    clk = Signal(bool(0))

    input_signal_list = [Signal(initial_val) for initial_val in initial_vals]
    
    if change_input_signal:

        for each_signal, initial_val in zip(input_signal_list, initial_vals):
            # Make sure it doesn't overflow when changing
            if initial_val > 0:
                each_signal.val[:] = initial_val - 1
            else:
                each_signal.val[:] = initial_val + 1

    if len(initial_vals[0]) == 1:
        output_signal_list = [
            Signal(intbv(not initial_val, min=0, max=2)) for 
            initial_val in initial_vals]
        update_val = int(not initial_vals[0])
    else:
        output_signal_list = [
            Signal(intbv(0, min=initial_val.min, max=initial_val.max)) for
            initial_val in initial_vals]
        update_val = 0

    expected_output = [each_input._init for each_input in input_signal_list]

    N = 10
    first = [True]

    signal_list_length = len(initial_vals)

    @instance
    def clkgen():

        clk.next = 0
        for n in range(N):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()
            
    @always_comb
    def output_driver():
        for i in range(signal_list_length):
            output_signal_list[i].next = input_signal_list[i]

    @always(clk.posedge)
    def drive_and_check():

        for i in range(signal_list_length):
            input_signal_list[i].next = update_val

        if __debug__:
            if first[0]:
                for i in range(signal_list_length):
                    assert output_signal_list[i] == expected_output[i]
                first[0] = False
            else:
                for i in range(signal_list_length):
                    assert output_signal_list[i] == update_val

    output_writer = canonical_list_writer(output_signal_list, clk)

    print output_writer.verilog_code
    return clkgen, output_driver, drive_and_check, output_writer

def runner(initial_val, change_input_signal=False):
    pre_toVerilog_initial_values = toVerilog.initial_values
    pre_toVHDL_initial_values = toVHDL.initial_values

    toVerilog.initial_values = True
    toVHDL.initial_values = True

    try:
        assert conversion.verify(
            initial_value_bench(initial_val, change_input_signal)) == 0
    
    finally:
        toVerilog.initial_values = pre_toVerilog_initial_values
        toVHDL.initial_values = pre_toVHDL_initial_values

def list_runner(initial_vals, change_input_signal=False):
    pre_toVerilog_initial_values = toVerilog.initial_values
    pre_toVHDL_initial_values = toVHDL.initial_values

    toVerilog.initial_values = True
    toVHDL.initial_values = True

    try:
        #foo = initial_value_list_bench(initial_vals, change_input_signal)
        #foo.convert()
        assert conversion.verify(
            initial_value_list_bench(initial_vals, change_input_signal)) == 0
        #foo = initial_value_list_bench(initial_vals, change_input_signal)
        #foo.convert()

    finally:
        toVerilog.initial_values = pre_toVerilog_initial_values
        toVHDL.initial_values = pre_toVHDL_initial_values


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

def test_modbv():
    '''The correct initial value should be used for modbv type signal.
    '''
    
    initial_val = modbv(randrange(0, 2**10))[10:]

    runner(initial_val)

def test_long_signals():
    '''The correct initial value should work with wide bitwidths (i.e. >32)
    '''
    min_val = -(2**71)
    max_val = 2**71 - 1
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val)

def test_single_length_signals():
    '''The correct initial value should be used for a single length signal
    '''
    initial_val = intbv(0, min=0, max=2)

    runner(initial_val)

def test_unsigned_list():
    '''The correct initial value should be used for unsigned type signal lists
    '''
    min_val = 0
    max_val = 34
    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val) 
        for each in range(10)]

    list_runner(initial_vals)


def test_signed_list():
    '''The correct initial value should be used for signed type signal lists
    '''
    min_val = -12
    max_val = 4
    
    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)
        for each in range(10)]

    list_runner(initial_vals)

def test_modbv_list():
    '''The correct initial value should be used for modbv type signal lists
    '''
    
    initial_vals = [
        modbv(randrange(0, 2**10))[10:] for each in range(10)]

    list_runner(initial_vals)

def test_long_signals_list():
    '''The correct initial value should work with wide bitwidths (i.e. >32) 
    signal lists
    '''
    min_val = -(2**71)
    max_val = 2**71 - 1
    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val) 
        for each in range(10)]

    list_runner(initial_vals)

def test_bool_signals_list():
    '''The correct initial value should be used for a boolean type signal lists
    '''
    initial_vals = [intbv(0, min=0, max=2) for each in range(10)]

    list_runner(initial_vals)


def test_init_used():
    '''It should be the _init attribute that is used for initialisation

    It should not be the current value, which should be ignored.
    '''
    min_val = -34
    max_val = 15
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val, change_input_signal=True)

#def test_init_used_list():
#    '''It should be the _init attribute of each element in the list 
#    that is used for initialisation
#
#    It should not be the current value, which should be ignored.
#    '''
#    min_val = -34
#    max_val = 15
#    initial_val = [intbv(
#        randrange(min_val, max_val), min=min_val, max=max_val) 
#        for each in range(10)]
#
#    list_runner(initial_val, change_input_signal=True)

if __name__ == "__main__":
    test_signed_list()


