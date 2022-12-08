import myhdl
from myhdl import *

@block
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

@block
def map_case2(z, a):

    @always_comb
    def logic():
        z.next = 0
        if a == 0:
            z.next = 0
        elif a == 1:
            z.next = 1

    return logic

@block
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

@block
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


@block
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

@block
def bool_bench_case(map_case):

    a = Signal(False)
    z = Signal(intbv(0)[2:])

    inst = map_case(z, a)

    @instance
    def stimulus():
        for i in range(2):
            a.next = i
            yield delay(10)
            print(z)

    return stimulus, inst

@block
def length1_bench_case(map_case):

    a = Signal(intbv(0)[1:])
    z = Signal(intbv(0)[2:])

    inst = map_case(z, a)

    @instance
    def stimulus():
        for i in range(2):
            a.next = i
            yield delay(10)
            print(z)

    return stimulus, inst

def test_case4():
    assert bench_case(map_case4, 4).verify_convert() == 0

def test_case2():
    assert bench_case(map_case2, 2).verify_convert() == 0

def test_case3():
    assert bench_case(map_case3, 3).verify_convert() == 0

def test_case4_full():
    assert bench_case(map_case4_full, 4).verify_convert() == 0

def test_case2_bool():
    assert bool_bench_case(map_case3).verify_convert() == 0

def test_case3_bool():
    assert bool_bench_case(map_case3).verify_convert() == 0

def test_case2_single_bit():
    assert length1_bench_case(map_case3).verify_convert() == 0

def test_case3_single_bit():
    assert length1_bench_case(map_case3).verify_convert() == 0
