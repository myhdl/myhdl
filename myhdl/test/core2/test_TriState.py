from __future__ import absolute_import
from myhdl import *


def bench_TristateSignal():
    s = TristateSignal(intbv(0)[8:])
    a = s.driver()
    b = s.driver()
    c = s.driver()

    @instance
    def check():
        assert s == Signal(None)
        a.next = 1
        yield delay(10)
        assert s == a
        a.next = None
        b.next = 122
        yield delay(10)
        assert s == b
        b.next = None
        c.next = 233
        yield delay(10)
        assert s == c
        c.next = None
        yield delay(10)
        assert s == Signal(None)

    return check


def test_TristateSignal():
    Simulation(bench_TristateSignal()).run()


def bench_TristateSignal_driver_list():
    s = TristateSignal(intbv(0)[8:])
    drivers = [s.driver() for i in range(10)]

    @instance
    def check():
        assert s == Signal(None)
        for i in downrange(9):
            drivers[i+1].next = None
            drivers[i].next = 0x55
            yield delay(10)
            assert s == Signal(intbv(0x55)[8:])

    return check


def test_TristateSignal_driver_list():
    Simulation(bench_TristateSignal_driver_list()).run()


def bench_TristateSignal_with_slice():
    s = TristateSignal(intbv(0)[8:])
    drivers = [s.driver() for i in range(10)]

    @instance
    def check():
        assert s == Signal(None)
        for i in downrange(9):
            drivers[i+1].next = None
            drivers[i].next = 0x55
            yield delay(10)
            slices = [s(i) for i in range(8)]
            for j in downrange(8):
                assert slices[j] == Signal(intbv(0x55)[8:])[j]

    return check


def test_TristateSignal_with_slice():
    Simulation(bench_TristateSignal_with_slice()).run()
