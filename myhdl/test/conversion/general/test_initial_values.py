from random import randrange

from myhdl import *
import myhdl

@block
def initial_value_enum_bench(initial_val, **kwargs):
    clk = Signal(bool(0))
    sig = Signal(initial_val)
    states = kwargs['states']
    N = 20

    if initial_val in (states.a, states.c):
        valid_states = (states.a, states.c)

    else:
        valid_states = (states.b, states.d)

    @instance
    def clkgen():

        clk.next = 0
        for n in range(N):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()

    @always(clk.posedge)
    def state_walker():
        if sig == states.a:
            sig.next = states.c
            print('a')
        elif sig == states.c:
            sig.next = states.a
            print('c')
        elif sig == states.b:
            sig.next = states.d
            print('b')
        elif sig == states.d:
            sig.next = states.b
            print('d')

        if __debug__:
            assert sig in valid_states

    return state_walker, clkgen

@block
def bool_writer(signal, clk):

    @always(clk.posedge)
    def writer():
        print(int(signal))

    return writer

@block
def int_writer(signal, clk):

    @always(clk.posedge)
    def writer():
        print(signal)

    return writer

@block
def initial_value_bench(initial_val, **kwargs):

    clk = Signal(bool(0))

    input_signal = Signal(initial_val)

    if 'change_input_signal' in kwargs.keys():

        change_input_signal = kwargs['change_input_signal']
    else:
        change_input_signal = False

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

    if isinstance(initial_val, bool):
        output_writer = bool_writer(output_signal, clk)

    else:
        output_writer = int_writer(output_signal, clk)


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
def bool_list_writer(output_signal_list, clk):

    signal_list_length = len(output_signal_list)

    @always(clk.posedge)
    def list_writer():
        for i in range(signal_list_length):
            print(int(output_signal_list[i]))

    return list_writer

@block
def initial_value_bool_list_bench(initial_vals, **kwargs):
    clk = Signal(bool(0))

    input_signal_list = [Signal(initial_val) for initial_val in initial_vals]

    output_signal_list = [
        Signal(not initial_val) for initial_val in initial_vals]

    update_val = int(not initial_vals[0])

    expected_output = [
        bool(each_input._init) for each_input in input_signal_list]

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

    output_writer = bool_list_writer(output_signal_list, clk)

    return clkgen, output_driver, drive_and_check, output_writer

@block
def assign_output(input_signal, output_signal):
    @always_comb
    def assignment():
        output_signal.next = input_signal

    return assignment

@block
def initial_value_list_bench(initial_vals, **kwargs):
    clk = Signal(bool(0))

    input_signal_list = [Signal(initial_val) for initial_val in initial_vals]

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

    # We assign each of the output drivers independently.
    # This forces the output to be a wire (where appropriate) so we can
    # check this type is handled properly too.
    output_drivers = []
    for input_signal, output_signal in zip(
        input_signal_list, output_signal_list):

        output_drivers.append(assign_output(input_signal, output_signal))

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

    return clkgen, output_drivers, drive_and_check, output_writer


@block
def initial_value_mem_convert_bench():

    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)
    wr = Signal(bool(0))
    wrd = Signal(intbv(0, min=0, max=32))
    rdd = Signal(intbv(0, min=0, max=32))
    addr = Signal(intbv(0, min=0, max=16))

    inst = memory(clock, reset, wr, wrd, rdd, addr)

    return inst


@block
def memory(clock, reset, wr, wrd, rdd, addr):

    mem = [Signal(intbv(0, min=wrd.min, max=wrd.max))
           for _ in range(addr.max)]

    inst_init = memory_init(mem)

    @always_seq(clock.posedge, reset=reset)
    def beh_mem():
        rdd.next = mem[addr]
        if wr:
            mem[addr].next = wrd

    return inst_init, beh_mem

@block
def memory_init(mem):
    mem_size = len(mem)
    init_values = tuple([int(ss.val) for ss in mem])

    with open("init_file.hex", 'w') as fp:
        for ii in range(mem_size):
            fp.write("CE \n")

    @instance
    def beh_init():
        for ii in range(mem_size):
            mem[ii].next = init_values[ii]
        yield delay(10)

    return beh_init


memory_init.verilog_code = """
    initial begin
        $$readmemh("init_file.hex", $mem, $mem_size);
    end
"""


def runner(initial_val, tb=initial_value_bench, **kwargs):
    pre_toVerilog_initial_values = toVerilog.initial_values
    pre_toVHDL_initial_values = toVHDL.initial_values

    toVerilog.initial_values = True
    toVHDL.initial_values = True

    try:
        assert conversion.verify(tb(initial_val, **kwargs)) == 0

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

def test_bool():
    '''The correct initial value should be used for bool type signal.
    '''
    initial_val = bool(randrange(0, 2))
    runner(initial_val)

def test_modbv():
    '''The correct initial value should be used for modbv type signal.
    '''

    initial_val = modbv(randrange(0, 2**10))[10:]

    runner(initial_val)

def test_enum():
    '''The correct initial value should be used for enum type signals.
    '''
    states = enum('a', 'b', 'c', 'd')
    val1 = states.c
    val2 = states.b

    runner(val1, tb=initial_value_enum_bench, states=states)
    runner(val2, tb=initial_value_enum_bench, states=states)

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

    runner(initial_vals, tb=initial_value_list_bench)

    # All the same case
    initial_vals = [
        intbv(randrange(min_val, max_val), min=min_val, max=max_val)] * 10
    runner(initial_vals, tb=initial_value_list_bench)

def test_signed_list():
    '''The correct initial value should be used for signed type signal lists
    '''
    min_val = -12
    max_val = 4

    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)
        for each in range(10)]

    runner(initial_vals, tb=initial_value_list_bench)

    # All the same case
    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)] * 10

    runner(initial_vals, tb=initial_value_list_bench)

def test_modbv_list():
    '''The correct initial value should be used for modbv type signal lists
    '''

    initial_vals = [
        modbv(randrange(0, 2**10))[10:] for each in range(10)]

    runner(initial_vals, tb=initial_value_list_bench)

    # All the same case
    initial_vals = [modbv(randrange(0, 2**10))[10:]] * 10
    runner(initial_vals, tb=initial_value_list_bench)


def test_long_signals_list():
    '''The correct initial value should work with wide bitwidths (i.e. >32)
    signal lists
    '''
    min_val = -(2**71)
    max_val = 2**71 - 1
    initial_vals = [intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)
        for each in range(10)]

    runner(initial_vals, tb=initial_value_list_bench)

    # All the same case
    initial_vals = [intbv(2**65-50, min=min_val, max=max_val)] * 10
    runner(initial_vals, tb=initial_value_list_bench)

def test_bool_signals_list():
    '''The correct initial value should be used for a boolean type signal lists
    '''
    initial_vals = [False for each in range(10)]

    runner(initial_vals, tb=initial_value_bool_list_bench)

    initial_vals = [False] * 10
    runner(initial_vals, tb=initial_value_bool_list_bench)


def test_init_used():
    '''It should be the _init attribute that is used for initialisation

    It should not be the current value, which should be ignored.
    '''
    min_val = -34
    max_val = 15
    initial_val = intbv(
        randrange(min_val, max_val), min=min_val, max=max_val)

    runner(initial_val, change_input_signal=True)


def test_memory_convert():
    inst = initial_value_mem_convert_bench()

    # TODO: this needs to be converted to use the `block` convert
    #       only and not modify the `toV*` but this will require
    #       changes to `conversion.verify` and `conversion.analyze`
    #       or a `config_conversion` function add to the `Block`.
    pre_xiv = toVerilog.initial_values
    pre_viv = toVHDL.initial_values

    # not using the runner, this test is setup for analyze only
    toVerilog.initial_values = True
    toVHDL.initial_values = True

    try:
        assert conversion.analyze(inst) == 0

    finally:
        toVerilog.initial_values = pre_xiv
        toVHDL.initial_values = pre_viv


@block
def init_reset_tb():

    clk = Signal(bool(0))
    reset = ResetSignal(0, active=1, isasync=False)

    s_large = Signal(intbv(0xc0000000)[32:])
    s_small = Signal(intbv(0xc)[32:])

    @instance
    def clkgen():

        clk.next = 0
        for n in range(10):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()

    @instance
    def raise_reset():
        yield clk.posedge
        reset.next = 1
        yield clk.posedge
        reset.next = 0

    @always_seq(clk.posedge,reset=reset)
    def seq():

        print(s_large)
        print(s_small)
        s_large.next = s_large + 1
        s_small.next = s_small + 1

    return instances()


def test_init_reset():
    """ Test assignment of initial values of signals used in an always_seq block with a reset signal
        Because the _convertInitVal in _toVHDL.py does special handling depending on the init value
        the test takes this into account.
    """

    inst = init_reset_tb()
    assert conversion.verify(inst,initial_values=True) == 0


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


