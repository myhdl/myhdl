from random import randrange

import myhdl
from myhdl import *

from bitonic import Array8Sorter, Array8Sorter_v

@block
def bench():

    n = 8
    w = 4

    a0, a1, a2, a3, a4, a5, a6, a7 = inputs = [Signal(intbv(0)[w:]) for i in range(n)]
    z0, z1, z2, z3, z4, z5, z6, z7 = outputs = [Signal(intbv(0)[w:]) for i in range(n)]


    inst = Array8Sorter_v(a0, a1, a2, a3, a4, a5, a6, a7,
                          z0, z1, z2, z3, z4, z5, z6, z7)

    @instance
    def check():
        for i in range(100):
            data = [randrange(2**w) for i in range(n)]
            for i in range(n):
                inputs[i].next = data[i]
            yield delay(10)
            data.sort()
            assert data == outputs

    return inst, check


def test_bench():
    bench().run_sim()

if __name__ == '__main__':
    test_bench()
