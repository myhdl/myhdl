from myhdl import (block, Signal, intbv, delay, always_comb, instance,
                   TristateSignal, ConcatSignal, conversion, StopSimulation,
                   toVerilog, toVHDL)


@block
def bench_SliceSignal():

    s = Signal(intbv(0)[8:])
    a, b, c = s(7), s(5), s(0)
    d, e, f, g = s(8, 5), s(6, 3), s(8, 0), s(4, 3)
    N = len(s)

    @instance
    def check():
        for i in range(N):
            s.next = i
            yield delay(10)
            print(int(a))
            print(int(b))
            print(int(c))
            print(d)
            print(e)
            print(f)
            print(g)

    return check


def test_SliceSignal():
    assert conversion.verify(bench_SliceSignal()) == 0


@block
def bench_RecurseShadowSignal():
    s = Signal(intbv(0)[16:])

    # take some recursive ShadowSignals
    su = s(16, 8)
    sl = s(8, 0)
    suu = su(8, 4)
    sul = su(4, 0)
    slu = sl(8, 4)
    sll = sl(4, 0)

    @instance
    def check():
        for i in range(25):
            s.next = 0x4567 + i * 39
            yield delay(10)
            print(s)
            print(int(su))
            print(int(sl))
            print(suu)
            print(sul)
            print(slu)
            print(sll)

    return check


def test_RecurseShadowSignal():
    assert conversion.verify(bench_RecurseShadowSignal()) == 0


@block
def bench_ConcatSignal():

    a = Signal(intbv(0)[5:])
    b = Signal(bool(0))
    c = Signal(intbv(0)[3:])
    d = Signal(intbv(0)[4:])

    s = ConcatSignal(a, b, c, d)

    I_max = 2 ** len(a)
    J_max = 2 ** len(b)
    K_max = 2 ** len(c)
    M_max = 2 ** len(d)

    @instance
    def check():
        for i in range(I_max):
            for j in range(J_max):
                for k in range(K_max):
                    for m in range(M_max):
                        a.next = i
                        b.next = j
                        c.next = k
                        d.next = m
                        yield delay(10)
                        print(s)

    return check


def test_ConcatSignal():
    assert conversion.verify(bench_ConcatSignal()) == 0


@block
def bench_ConcatSignalWithConsts():

    a = Signal(intbv(0)[5:])
    b = Signal(bool(0))
    c = Signal(intbv(0)[3:])
    d = Signal(intbv(0)[4:])
    e = Signal(intbv(0)[1:])

    c1 = "10"
    c2 = intbv(3)[3:]
    c3 = '0'
    c4 = bool(1)
    c5 = intbv(42)[8:]  # with leading zeroes

    s = ConcatSignal(c1, a, c2, b, c3, c, c4, d, c5, e)

    I_max = 2 ** len(a)
    J_max = 2 ** len(b)
    K_max = 2 ** len(c)
    M_max = 2 ** len(d)

    @instance
    def check():
        for i in range(I_max):
            for j in range(J_max):
                for k in range(K_max):
                    for m in range(M_max):
                        for n in range(2 ** len(e)):
                            a.next = i
                            b.next = j
                            c.next = k
                            d.next = m
                            e.next = n
                            yield delay(10)
                            print(s)

    return check


def test_ConcatSignalWithConsts():
    assert conversion.verify(bench_ConcatSignalWithConsts()) == 0

@block
def bench_ConcatSignalUndriven():

    n_sigs = 32

    sig_list = [Signal(False) for n in range(n_sigs)]
    concat_sig = ConcatSignal(*reversed(sig_list))

    @instance
    def check():

        yield delay(10)
        print(concat_sig)

    return check

def test_ConcatSignalUndriven():
    assert conversion.verify(bench_ConcatSignalUndriven()) == 0

@block
def bench_TristateSignal():
    s = TristateSignal(intbv(0)[8:])
    a = s.driver()
    b = s.driver()
    c = s.driver()

    @instance
    def check():
        a.next = None
        b.next = None
        c.next = None
        yield delay(10)
        # print s
        a.next = 1
        yield delay(10)
        print(s)
        a.next = None
        b.next = 122
        yield delay(10)
        print(s)
        b.next = None
        c.next = 233
        yield delay(10)
        print(s)
        c.next = None
        yield delay(10)
        # print s

    return check


def test_TristateSignal():
    assert conversion.verify(bench_TristateSignal()) == 0


@block
def permute(x, a, mapping):

    p = [a(m) for m in mapping]

    q = ConcatSignal(*p)

    @always_comb
    def assign():
        x.next = q

    return assign


@block
def bench_permute(conv=False):

    x = Signal(intbv(0)[3:])
    a = Signal(intbv(0)[3:])
    mapping = (0, 2, 1)

    if conv:
        dut = conv(permute(x, a, mapping))
    else:
        dut = permute(x, a, mapping)

    @instance
    def stimulus():
        for i in range(2 ** len(a)):
            a.next = i
            yield delay(10)
            print("%d %d" % (x, a))
            assert x[2] == a[0]
            assert x[1] == a[2]
            assert x[0] == a[1]
        raise StopSimulation()

    return dut, stimulus


def test_permute():
    assert conversion.verify(bench_permute()) == 0


bench_permute(toVHDL)
bench_permute(toVerilog)
