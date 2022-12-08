
import sys

import myhdl
from myhdl import (block, Signal, ResetSignal, modbv, always_seq, concat,
                   instance, delay, StopSimulation)
from myhdl.conversion import analyze, verify

"""
This set of tests exercises a peculiar scenario where an expanded
interface Signal is flagged as having multiple drivers.  This appears
to be a name collision in the name expansion and was introduced in
08519b4.
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
def use_nested_intf(clock, reset, intf1, intf2):
    
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
        intf2.intf.sig1.next = intf2.sig2
        intf2.intf.sig2.next = intf2.intf.sig1

    return proc


@block
def something_peculiar(clock, reset, intf1, intf2):

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
def interfaces_top(clock, reset, sdi, sdo, nested):
    
    intf1, intf2, intf3 = Intf1(), Intf2(), Intf1()

    inst1 = use_nested_intf(clock, reset, intf1, intf2)
    inst2 = something_peculiar(clock, reset, intf2, intf3)

    @always_seq(clock.posedge, reset)
    def assigns():
        intf1.sig1.next = sdi
        intf1.sig2.next = not sdi
        intf1.sig3.next = concat(intf1.sig3[7:1], sdi)
        sdo.next = intf3.sig1 | intf3.sig2 | intf3.sig3[2]
        nested.next = intf2.intf.sig2

    return inst1, inst2, assigns


@block
def c_testbench_one():
    """ yet another interface test.
    This test is used to expose a particular bug that was discovered
    during the development of interface conversion.  The structure
    used in this example caused and invalid multiple driver error.
    """
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, isasync=False)
    sdi = Signal(bool(0))
    sdo = Signal(bool(0))
    nested = Signal(bool())
    tbdut = interfaces_top(clock, reset, sdi, sdo, nested)

    @instance    
    def tbclk():
        clock.next = False
        while True:
            yield delay(3)
            clock.next = not clock
     
    # there is an issue when using bools with variables and
    # VHDL conversion, this might be an expected limitation?
    # expected = (False, False, False, True, True, True,
    #             False, True, False, True)
    # use a tuple-of-ints instead of the above tuple-of-bools
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
            print("sdi: %d, sdo: %d, nested: %d" % (sdi, sdo, nested))
            expected_bit = expected[ii]
            assert sdo == expected_bit
            sdi.next = not sdi
            yield clock.posedge

        raise StopSimulation

    return tbclk, tbstim, tbdut


def test_one_testbench():
    inst = c_testbench_one()
    inst.run_sim()


def test_one_analyze():
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, isasync=False)
    sdi = Signal(bool(0))
    sdo = Signal(bool(0))
    nested = Signal(bool(0))
    assert analyze(interfaces_top(clock, reset, sdi, sdo, nested)) == 0


def test_one_verify():
    assert verify(c_testbench_one()) == 0


def test_conversion():
    inst = c_testbench_one()
    inst.convert(hdl='Verilog')
    inst.convert(hdl='VHDL')
