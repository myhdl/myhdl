from myhdl import *

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
                        assert s[16:8] == a
                        assert s[7] == b
                        assert s[7:4] == c
                        assert s[4:] == d

    return check


def test_ConcatSignal():
    Simulation(bench_ConcatSignal()).run()




