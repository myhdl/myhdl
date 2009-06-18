from myhdl import *

def bench_AssignSignal():
    a = Signal(bool(0))
    p = Signal(bool(0))
    b = Signal(intbv(0)[8:])
    q = Signal(intbv(0)[8:])


    p.assign(a)
    q.assign(b)

    @instance
    def stimulus():
        a.next = 0
        b.next = 0
        yield delay(10)
        for i in range(len(b)):
            b.next = i
            a.next = not a
            yield delay(10)
            print int(p)
            print q

    return stimulus

def test_AssignSignal():
    assert conversion.verify(bench_AssignSignal) == 0

