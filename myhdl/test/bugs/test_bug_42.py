#! /usr/bin/env python

import myhdl
from myhdl import *

@block
def module_42(sigin, sigout):

    # Using @always(sigin) only warns, but using @always_comp breaks.
    # The reason is that len(sigout) is interpreted as sigout being used as
    # an input.
    #@always(sigin)
    @always_comb
    def output():
         sigout.next = sigin[len(sigout):]

    return output

sigin = Signal(intbv(0)[2:])
sigout = Signal(intbv(0)[2:])

def test_bug_42():
    module_42(sigin, sigout).convert(hdl='VHDL')

