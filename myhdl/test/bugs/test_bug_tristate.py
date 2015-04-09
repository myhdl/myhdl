from __future__ import absolute_import
from myhdl import *


def bench_bug_concat_tristate():
    """ We are unable to concat Tristate signal bus
    before the value is assigned to driver
    because NoneType is incompatible with concat
    """
    s = TristateSignal(intbv(0)[8:])
    drivers = [s.driver() for i in range(10)]
    drivers = concat(*drivers)

    @instance
    def check():
        assert s == Signal(None)
        for i in downrange(9):
            for j in downrange(8):
                drivers[8*i + j + 1].next = None
                drivers[8*i + j].next = True
                yield delay(10)
                assert s == Signal(intbv(2**j)[8:])

    return check


def test_bug_concat_tristate():
    Simulation(bench_bug_concat_tristate()).run()


def bench_bug_slice_tristate():
    """ We are unable to slice Tristate signal
    before the value is assigned to any driver
    because NoneType cannot be sliced.
    """
    s = TristateSignal(intbv(0)[8:])
    drivers = [s.driver() for i in range(10)]
    slices = [s(i) for i in range(8)]

    @instance
    def check():
        assert s == Signal(None)
        for i in downrange(9):
            drivers[i+1].next = None
            drivers[i].next = 0x55
            for j in downrange(8):
                assert slices[j] == Signal(intbv(0x55)[8:])[j]

    return check


def test_bug_slice_tristate():
    Simulation(bench_bug_slice_tristate()).run()


def bench_bug_slice_tristate2():
    """ If Tristate signal is sliced after
    value is assigned to the bus, the slices
    does not hold value after Tristate is value
    is driven by another driver.
    """
    s = TristateSignal(intbv(0)[8:])
    drivers = [s.driver() for i in range(10)]

    @instance
    def check():
        assert s == Signal(None)
        drivers[9].next = 0xAA
        yield delay(10)
        slices = [s(i) for i in range(8)]
        for i in downrange(9):
            drivers[i+1].next = None
            drivers[i].next = 0x55
            for j in downrange(8):
                assert slices[j] == Signal(intbv(0x55)[8:])[j]

    return check


def test_bug_slice_tristate2():
    Simulation(bench_bug_slice_tristate2()).run()
