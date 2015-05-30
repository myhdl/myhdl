from __future__ import absolute_import
from myhdl import *

def map_case4(z, a):

    @always_comb
    def logic():
        if a == 0:
            z.next = 0
        elif a == 1:
            z.next = 1
        elif a == 2:
            z.next = 2
        else:
            z.next = 3

    return logic

def map_case2(z, a):

    @always_comb
    def logic():
        z.next = 0
        if a == 0:
            z.next = 0
        elif a == 1:
            z.next = 1

    return logic


def map_case3(z, a):

    @always_comb
    def logic():
        if a == 0:
            z.next = 0
        elif a == 1:
            z.next = 1
        else:
            z.next = 2

    return logic

def map_case4_full(z, a):

    @always_comb
    def logic():
        if a == 0:
            z.next = 0
        elif a == 1:
            z.next = 1
        elif a == 2:
            z.next = 2
        elif a == 3:
            z.next = 3

    return logic


def bench_case(map_case, N):

    a = Signal(intbv(0)[2:])
    z = Signal(intbv(0)[2:])

    inst = map_case(z, a)

    @instance
    def stimulus():
        for i in range(N):
            a.next = i
            yield delay(10)
            print(z)

    return stimulus, inst


def test_case4():
    assert conversion.verify(bench_case, map_case4, 4) == 0

def test_case2():
    assert conversion.verify(bench_case, map_case2, 2) == 0

def test_case3():
    assert conversion.verify(bench_case, map_case3, 3) == 0

def test_case4_full():
    assert conversion.verify(bench_case, map_case4_full, 4) == 0

