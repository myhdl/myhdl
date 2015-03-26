from __future__ import absolute_import

from random import randint

from myhdl import *
from myhdl.conversion import verify

def m_int_case(clock, reset, x, y):
 
    @always_seq(clock.posedge, reset=reset)
    def rtl():
        z = (x >> 16) & 0x3
        if z == 0:
            y.next = y + 0xDECAFBAD
        elif z == 1:
            y.next = x + 0xC0FFEE
        elif z == 2:
            y.next = y + 2
        else:
            y.next = 299792458

    return rtl

 
def c_testbench():
    """ convertible testbench """
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=False)
    x = Signal(intbv(0, min=0, max=444356))
    y = Signal(intbv(0)[32:])

    tbdut = m_int_case(clock, reset, x, y)

    @instance
    def tbclk():
        clock.next = False
        while True:
            yield delay(3)
            clock.next = not clock

    @instance
    def tbstim():
        reset.next = reset.active
        yield delay(11)
        reset.next = not reset.active

        # this is a converion issue, test a couple cases to
        # make sure the module is accurate
        
        # value after reset
        yield clock.posedge
        assert y == 0
        x.next = 0x17777

        yield clock.posedge
        assert y == 0xDECAFBAD
        x.next = 0x20000

        yield clock.posedge
        assert y == (0x17777 + 0xC0FFEE)
        yc = int(y)
        x.next = 0x39999

        yield clock.posedge
        assert y == (yc + 2)

        yield clock.posedge
        assert y == 299792458

        raise StopSimulation

    return tbdut, tbclk, tbstim


def test_github_issue_44_sim():
    Simulation(c_testbench()).run()

def test_github_issue_44():
    assert verify(c_testbench) == 0

if __name__ == '__main__':
    test_github_issue_44_sim()