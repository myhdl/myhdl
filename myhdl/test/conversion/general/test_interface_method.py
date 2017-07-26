from __future__ import absolute_import

import sys

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

class simple_interface(object):
    def __init__(self):
        self.x = Signal(intbv(0, min=0, max=16))

    def inc(self):
        return self.x + 1

@block
def simple_do(clk, reset, in_x, in_y):

    i = simple_interface()
    @always_seq(clk.posedge, reset = reset)
    def inc_caller():
        i.inc()

    return inc_caller

@block
def testbench_one():
    #TODO: implement this
    pass

@block
def test_simple_do_analyze():
    #TODO: implement this
    pass

@block
def test_simple_do_verify():
    #TODO: implement this
    pass


if __name__ == '__main__':
    #TODO: implement this
    pass
