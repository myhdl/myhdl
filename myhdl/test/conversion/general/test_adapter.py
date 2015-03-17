from __future__ import absolute_import
from myhdl import *

def adapter(o_err, i_err, o_spec, i_spec):

    nomatch = Signal(bool(0))
    other = Signal(bool(0))

    o_err_bits = []
    for s in o_spec:
        if s == 'other':
            o_err_bits.append(other)
        elif s == 'nomatch':
            o_err_bits.append(nomatch)
        else:
            bit = i_err(i_spec[s])
            o_err_bits.append(bit)
    o_err_vec = ConcatSignal(*o_err_bits)

    other_bits = []
    for s, i in i_spec.items():
        if s in o_spec:
            continue
        bit = i_err(i)
        other_bits.append(bit)
    other_vec = ConcatSignal(*other_bits)

    @always_comb
    def assign():
        nomatch.next = 0
        other.next = (other_vec != 0)
        o_err.next = o_err_vec

    return assign


def bench_adapter(conv=False):
    o_spec = ('c', 'a', 'other', 'nomatch')
    i_spec = { 'a' : 1, 'b' : 2, 'c' : 0, 'd' : 3, 'e' : 4, 'f' : 5, }

    o_err = Signal(intbv(0)[4:])
    i_err = Signal(intbv(0)[6:])
    
    if conv:
        dut = conv(adapter, o_err, i_err, o_spec, i_spec)
    else:
        dut = adapter(o_err, i_err, o_spec, i_spec)

    N = 2**len(i_err)
    @instance
    def stimulus():
        for i in range(N):
            i_err.next = i
            yield delay(10)
            assert o_err[0] == 0
            assert o_err[1] == (i_err[2] | i_err[3] | i_err[4] | i_err[5])
            assert o_err[2] == i_err[1]
            assert o_err[3] == i_err[0]
            print(o_err)

    return dut, stimulus

def test_adapter():
    assert conversion.verify(bench_adapter) == 0


bench_adapter(toVerilog)
bench_adapter(toVHDL)
