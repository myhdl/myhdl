from myhdl import *

def bench_ShadowSignal():
    
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


def test_ShadowSignal():
    Simulation(bench_ShadowSignal()).run()

