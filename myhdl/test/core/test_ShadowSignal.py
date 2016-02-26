from __future__ import absolute_import

from myhdl import *
from myhdl._compat import long


def bench_SliceSignal():

    s = Signal(intbv(0)[8:])
    a, b, c = s(7), s(5), s(0)
    d, e, f, g = s(8,5), s(6,3), s(8,0), s(4,3)

    @instance
    def check():
        for i in range(2**len(s)):
            s.next = i
            yield delay(10)
            assert s[7] == a
            assert s[5] == b
            assert s[0] == c
            assert s[8:5] == d
            assert s[6:3] == e
            assert s[8:0] == f
            assert s[4:3] == g

    return check


def test_SliceSignal():
    Simulation(bench_SliceSignal()).run()


def bench_ConcatSignal():

    a = Signal(intbv(0)[5:])
    b = Signal(bool(0))
    c = Signal(intbv(0)[3:])
    d = Signal(intbv(0)[4:])

    s = ConcatSignal(a, b, c, d)

    @instance
    def check():
        for i in range(2**len(a)):
            for j in (0, 1):
                for k in range(2**len(c)):
                    for m in range(2**len(d)):
                        a.next = i
                        b.next = j
                        c.next = k
                        d.next = m
                        yield delay(10)
                        assert s[13:8] == a
                        assert s[7] == b
                        assert s[7:4] == c
                        assert s[4:] == d

    return check


def test_ConcatSignal():
    Simulation(bench_ConcatSignal()).run()


def bench_ConcatSignalWithConsts():

    a = Signal(intbv(0)[5:])
    b = Signal(bool(0))
    c = Signal(intbv(0)[3:])
    d = Signal(intbv(0)[4:])
    e = Signal(intbv(0)[1:])

    c1 = "10"
    c2 = '0'
    c3 = intbv(5)[3:]
    c4 = bool(1)
    c5 = intbv(42)[8:]  # with leading zeroes

    s = ConcatSignal(c1, a, c2, b, c3, c, c4, d, c5, e)

    @instance
    def check():
        for i in range(2**len(a)):
            for j in (0, 1):
                for k in range(2**len(c)):
                    for m in range(2**len(d)):
                        for n in range(2**len(e)):
                            a.next = i
                            b.next = j
                            c.next = k
                            d.next = m
                            e.next = n
                            yield delay(10)
                            assert s[29:27] == long(c1, 2)
                            assert s[27:22] == a
                            assert s[21] == long(c2, 2)
                            assert s[20] == b
                            assert s[20:17] == c3
                            assert s[17:14] == c
                            assert s[13] == c4
                            assert s[13:9] == d
                            assert s[9:1] == c5
                            assert s[1:] == e

    return check


def test_ConcatSignalWithConsts():
    Simulation(bench_ConcatSignalWithConsts()).run()

def bench_ConcatSignalWithNegs():

    Am = 2**(5-1)
    Cm = 2**(3-1)
    Dm = 2**(4-1)

    a = Signal(intbv(-1, min=-Am, max=Am))
    b = Signal(bool(0))
    c = Signal(intbv(-1, min=-Cm, max=Cm))
    d = Signal(intbv(-1, min=-Dm, max=Dm))

    s = ConcatSignal(a, b, c, d)

    @instance
    def check():
        for i in range(-Am, Am):
            for j in (0, 1):
                for k in range(-Cm, Cm):
                    for m in range(-Dm, Dm):
                        a.next = i
                        b.next = j
                        c.next = k
                        d.next = m
                        yield delay(10)
                         
                        assert s[13:8] == a[len(a):]
                        assert s[7] == b
                        assert s[7:4] == c[len(c):]
                        assert s[4:] == d[len(d):]

    return check

def test_ConcatSignalWithNegs():
    Simulation(bench_ConcatSignalWithNegs()).run()


def bench_TristateSignal():
    s = TristateSignal(intbv(0)[8:])
    a = s.driver()
    b = s.driver()
    c = s.driver()

    @instance
    def check():
        assert s == None
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
        assert s == None

    return check


def test_TristateSignal():
    Simulation(bench_TristateSignal()).run()
