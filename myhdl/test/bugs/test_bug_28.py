from __future__ import absolute_import
from myhdl import *

def bug_28(dout, channel):
    @always_comb
    def comb():
        dout.next = 0x8030 + (channel << 10)
    return comb

dout = Signal(intbv(0)[16:0])
channel = Signal(intbv(0)[4:0])

def test_bug_28():
    try:
        toVHDL(bug_28, dout, channel)
    except:
        raise
