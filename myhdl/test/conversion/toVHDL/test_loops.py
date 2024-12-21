import os
path = os.path
from random import randrange

from myhdl import (block, Signal, intbv, delay, instance)
from myhdl import ConversionError
from myhdl.conversion._misc import _error


@block
def ForLoopError1(a, out):

    @instance
    def comb():
        while 1:
            yield a
            var = 0
            for i in range(1, 4, 3):
                if a[i] == 1:
                    var += 1
            out.next = var

    return comb


@block
def LoopBench(LoopTest):

    a = Signal(intbv(-1)[16:])
    z = Signal(intbv(0)[16:])

    looptest_inst = LoopTest(a, z)
    data = tuple([randrange(2 ** min(i, 16)) for i in range(100)])

    @instance
    def stimulus():
        for i in range(100):
            a.next = data[i]
            yield delay(10)
            print(z)

    return stimulus, looptest_inst


def testForLoopError1():
    try:
        LoopBench(ForLoopError1).analyze_convert()
    except ConversionError as e:
        assert e.kind == _error.Requirement
    else:
        assert False

