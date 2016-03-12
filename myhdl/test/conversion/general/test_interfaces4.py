from __future__ import absolute_import

import sys

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze, verify

import myhdl
from myhdl import *

"""
This set of tests exercies a peculiar scenario where an
expanded interface Signal is flagged as having multiple
drivers.  This appears to be a name collision in the name
expansion and was introduced in 08519b4.  
"""

class Intf1(object):
    def __init__(self):
        self.sig1 = Signal(bool(0))
        self.sig2 = Signal(bool(0))
        self.sig3 = Signal(modbv(0)[8:])


class Intf2(object):
    def __init__(self):
        self.sig1 = Signal(bool(0))
        self.sig2 = Signal(bool(0))
        self.sig3 = Signal(modbv(0)[8:])
        self.intf = Intf1()

@block
def mod1(clock, reset, intf1, intf2):
    
    sig1 = Signal(bool(0))
    sig2 = Signal(bool(0))
    @always_seq(clock.posedge, reset)
    def proc():
        if intf1.sig1:
            sig1.next = True
            sig2.next = False
        else:
            sig1.next = False
            sig2.next = True

        intf2.sig1.next = sig1
        intf2.sig2.next = sig2 or intf1.sig2
        intf2.sig3.next = ~intf1.sig3

    return proc


@block
def mod2(clock, reset, intf1, intf2):
    @always_seq(clock.posedge, reset)
    def proc():
        # remove the if/else and leave just the line in the
        # if clause the error does not occur, inlcude the if/else
        # and the error occurs
        if intf1.sig3 > 0:        # remove no error
            intf2.sig1.next = not intf1.sig1
            intf2.sig2.next = not intf1.sig2
            intf2.sig3.next = intf1.sig3 + intf2.sig3
        else:                     # remove no error
            intf2.sig3.next = 0   # remove no error

    return proc


@block
def m_top(clock, reset, sdi, sdo):
    
    intf1 = Intf1()
    intf2 = Intf2()
    intf3 = Intf1()

    g1 = mod1(clock, reset, intf1, intf2)
    g2 = mod2(clock, reset, intf2, intf3)

    @always_seq(clock.posedge, reset)
    def assigns():
        intf1.sig1.next = sdi
        intf1.sig2.next = not sdi
        intf1.sig3.next = concat(intf1.sig3[7:1], sdi)
        sdo.next = intf3.sig1 | intf3.sig2 | intf3.sig3[2]

    return g1, g2, assigns


@block
def c_testbench_one():
    """ yet another interface test.
    This test is used to expose a particular bug that was discovered
    during the development of interface conversion.  The structure
    used in this example caused and invalid multiple driver error.
    """
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, async=False)
    sdi = Signal(bool(0))
    sdo = Signal(bool(0))
    tbdut = m_top(clock, reset, sdi, sdo)

    @instance    
    def tbclk():
        clock.next = False
        while True:
            yield delay(3)
            clock.next = not clock
     
    # there is an issue when using bools with varialbes and
    # VHDL conversion, this might be an expected limitation?
    #expected = (False, False, False, True, True, True,
    #            False, True, False, True)
    expected = (0, 0, 0, 1, 1, 1, 0, 1, 0, 1)

    ra = reset.active    
    @instance
    def tbstim():
        sdi.next = False
        reset.next = ra
        yield delay(13)
        reset.next = not ra
        yield clock.posedge
        for ii in range(10):
            print("sdi: %d, sdo: %d" % (sdi, sdo))
            expected_bit = expected[ii]
            assert sdo == expected_bit
            sdi.next = not sdi
            yield clock.posedge

        raise StopSimulation

    return tbclk, tbstim, tbdut


def test_one_testbench():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, async=False)
    sdi = Signal(bool(0))
    sdo = Signal(bool(0))
    Simulation(c_testbench_one()).run()


def test_one_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, async=False)
    sdi = Signal(bool(0))
    sdo = Signal(bool(0))
    analyze(m_top(clock, reset, sdi, sdo))


def test_one_verify():
    assert verify(c_testbench_one()) == 0


def test_conversion():
    toVerilog(c_testbench_one())
    toVHDL(c_testbench_one())


if __name__ == '__main__':
    print(sys.argv[1])
    verify.simulator = analyze.simulator = sys.argv[1]
    print("*** verify example testbench ")
    test_one_testbench()
    print("*** verify example module conversion ")
    test_one_analyze()
    print("*** test testbench conversion ")
    test_conversion()
    print("*** verify testbench conversion and execution")
    test_one_verify()
    
