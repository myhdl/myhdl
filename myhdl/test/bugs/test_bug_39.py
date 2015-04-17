from __future__ import absolute_import
from myhdl import *
from myhdl.conversion import verify

def dut():

    rx = Signal(intbv(0, min=-512, max=512))
    a = Signal(intbv(0, min=0, max=256))
    b = Signal(intbv(0, min=0, max=256))
    c = Signal(intbv(0, min=0, max=256))
    d = Signal(intbv(0, min=0, max=256))
    
    @always_comb
    def logic():
        rx.next = a + b - (c + d)

    @instance
    def check():
        a.next = 0
        b.next = 0
        c.next = 0
        d.next = 0
        for i in range(100):
            yield delay(10)
            print(rx)
            a.next = (a + 37) % 256
            b.next = (b + 67) % 256
            c.next = (c + 97) % 256
            d.next = (d + 137) % 256

    return logic, check

def test_bug_39():
    assert verify(dut) == 0


