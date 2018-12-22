'''
Created on 22 dec. 2018

@author: josy

testing signed ShadowSignals 
'''

from __future__ import absolute_import

import random
random.seed('We want repeatable randomness')

from myhdl import Signal, intbv, ConcatSignal, instance, delay, block, conversion


@block
def bench_SliceSignalSigned():

    a, c = [Signal(intbv(random.randint(-128, 127), min=-2 ** 7, max=2 ** 7)) for _ in range(2)]
    b, d = [Signal(intbv(0)[8:]) for _ in range(2)]
    s = ConcatSignal(d, c, b, a)
    e, g = [s((i + 1) * 8, i * 8, signed=True) for i in range(0, 4, 2)]
    f, h = [s((i + 1) * 8, i * 8) for i in range(1, 4, 2)]

    aa = Signal(intbv(0, -256, 256))

    @instance
    def check():
        a.next = -1
        b.next = 1
        c.next = 42
        d.next = 0xcc
        yield delay(10)
        print(s)
        print(int(e))
        print(f)
        print(int(g))
        print(h)
        aa.next = e + f
        print(aa)

        a.next = 127
        b.next = 0xaa
        c.next = -128
        d.next = 0x55
        yield delay(10)
        print(s)
        print(int(e))
        print(f)
        print(int(g))
        print(h)

    return check


def test_SliceSignalSigned():
    assert conversion.verify(bench_SliceSignalSigned()) == 0


if __name__ == '__main__':
    dfc = bench_SliceSignalSigned()
    dfc.convert(hdl='VHDL')
    dfc.convert(hdl='Verilog')
    dfc.run_sim()

