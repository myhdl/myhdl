from __future__ import absolute_import
import os
path = os.path
from random import randrange

from myhdl import *
from myhdl.conversion import verify, analyze
from myhdl import ConversionError
from myhdl.conversion._misc import _error

def ForLoopError1(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in range(1, 4, 3):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic


def LoopBench(LoopTest):

    a = Signal(intbv(-1)[16:])
    z = Signal(intbv(0)[16:])

    looptest_inst = LoopTest(a, z)
    data = tuple([randrange(2**min(i, 16)) for i in range(100)])

    @instance
    def stimulus():
        for i in range(100):
            a.next = data[i]
            yield delay(10)
            print z

    return stimulus, looptest_inst


def testForLoopError1():
    try:
        analyze(LoopBench, ForLoopError1)
    except ConversionError as e:
        assert e.kind == _error.Requirement
    else:
        assert False
    
    

