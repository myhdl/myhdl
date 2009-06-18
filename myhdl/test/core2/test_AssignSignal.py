from myhdl import *

def bench_AssignSignal():
    a = Signal(bool(0))
    p = Signal(bool(0))
    b = Signal(intbv(0)[8:])
    q = Signal(intbv(0)[10:])


    p.assign(a)
    q.assign(b)

    @instance
    def stimulus():
        for i in range(len(b)):
            b.next = i
            a.next = not a
            yield delay(10)
            assert p == a
            assert q == b

    return stimulus

def test_AssignSignal():
    Simulation(bench_AssignSignal()).run()

