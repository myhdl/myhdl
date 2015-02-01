from __future__ import absolute_import
#! /usr/bin/env python

from myhdl import *

def module(sigin, sigout):

    # Using @always(sigin) only warns, but using @always_comp breaks.
    # The reason is that len(sigout) is interpreted as sigout being used as
    # an input.
    @always(sigin)
    def output():
         sigout.next = sigin[len(sigout):]

    return output

sigin = Signal(intbv(0)[2:])
sigout = Signal(intbv(0)[2:])

def test_bug_42_2():
    toVHDL(module, sigin, sigout)

toVHDL(module, sigin, sigout)


