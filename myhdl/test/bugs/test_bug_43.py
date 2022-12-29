#! /usr/bin/env python

import myhdl
from myhdl import *

@block
def bug_43(sigin, sigout):

    @always_comb
    def output():
         # This does not generate correct VHDL code (resize is missing)
         sigout.next = concat(sigin[0], sigin[2])

         # The following does work:
         tmp = concat(sigin[0], sigin[2])
         sigout.next = tmp

    return output

def test_bug_43():
    sigin = Signal(intbv(0)[4:])
    sigout = Signal(intbv(0)[4:])

    assert bug_43(sigin, sigout).analyze_convert() == 0


