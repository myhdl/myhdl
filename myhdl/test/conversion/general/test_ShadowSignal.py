from myhdl import *

def bench_ShadowSignal():
    
    s = Signal(intbv(0)[8:])
    a, b, c = s(7), s(5), s(0)
    d, e, f, g = s(8,5), s(6,3), s(8,0), s(4,3)
    N = len(s) 

    @instance
    def check():
        for i in range(N):
            s.next = i
            yield delay(10)
            print int(a)
            print int(b)
            print int(c)
            print d
            print e
            print f
            print g

    return check


def test_ShadowSignal():
    assert conversion.verify(bench_ShadowSignal) == 0

