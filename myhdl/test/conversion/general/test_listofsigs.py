from __future__ import absolute_import
import pytest
import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

N = 8
M= 2**N


### A first case that already worked with 5.0 list of signal constraints ###

@pytest.mark.verify_convert
@block
def test_intbv2list():
    """Conversion between intbv and list of boolean signals."""
    
    a = Signal(intbv(0)[N:])
    b = [Signal(bool(0)) for i in range(len(a))]
    z = Signal(intbv(0)[N:])

    @always(a)
    def extract():
        for i in range(len(a)):
            b[i].next = a[i]

    @always(*b)
    def assemble():
        for i in range(len(b)):
            z.next[i] = b[i]

    @instance
    def stimulus():
        for i in range(M):
            a.next = i
            yield delay(10)
            assert z == a
            print(a)
        raise StopSimulation

    return extract, assemble, stimulus

    
### A number of cases with relaxed constraints, for various decorator types ###

@block
def inv1(z, a):
    @always(a)
    def logic():
        z.next = not a
    return logic


@block
def inv2(z, a):
    @always_comb
    def logic():
        z.next = not a
    return logic


@block
def inv3(z, a):
    @instance
    def logic():
        while True:
            yield a
            z.next = not a
    return logic

@block
def inv4(z, a):
    @instance
    def logic():
        while True:
            yield a
            yield delay(1)
            z.next = not a
    return logic


@block
def case1(z, a, inv):
    b = [Signal(bool(1)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    @always(a)
    def extract():
        for i in range(len(a)):
            b[i].next = a[i]

    inst = [None] * len(b)
    for i in range(len(b)):
        inst[i] = inv(c[i], b[i])

    @always(*c)
    def assemble():
        for i in range(len(c)):
            z.next[i] = c[i]

    return extract, inst, assemble


@block
def case2(z, a, inv):
    b = [Signal(bool(1)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    @always_comb
    def extract():
        for i in range(len(a)):
            b[i].next = a[i]

    inst = [None] * len(b)
    for i in range(len(b)):
        inst[i] = inv(c[i], b[i])

    @always_comb
    def assemble():
        for i in range(len(c)):
            z.next[i] = c[i]

    return extract, inst, assemble


@block
def case3(z, a, inv):
    b = [Signal(bool(1)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    @instance
    def extract():
        while True:
            yield a
            for i in range(len(a)):
                b[i].next = a[i]

    inst = [None] * len(b)
    for i in range(len(b)):
        inst[i] = inv(c[i], b[i])

    @instance
    def assemble():
        while True:
            yield c
            for i in range(len(c)):
                z.next[i] = c[i]

    return extract, inst, assemble


@block
def case4(z, a, inv):
    b = [Signal(bool(1)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    @instance
    def extract():
        while True:
            yield a
            yield delay(1)
            for i in range(len(a)):
                b[i].next = a[i]

    inst = [None] * len(b)
    for i in range(len(b)):
        inst[i] = inv(c[i], b[i])

    @instance
    def assemble():
        while True:
            yield c
            yield delay(1)
            for i in range(len(c)):
                z.next[i] = c[i]

    return extract, inst, assemble


@pytest.mark.parametrize('case, inv', [
    (case1, inv1),
    (case1, inv2),
    (case2, inv2),
    (case3, inv3),
    (case4, inv4)
])
@pytest.mark.verify_convert
@block
def test_processlist(case, inv):
    """Extract list from intbv, do some processing, reassemble."""
    
    a = Signal(intbv(1)[N:])
    z = Signal(intbv(0)[N:])

    case_inst = case(z, a, inv)

    @instance
    def stimulus():
        for i in range(M):
            yield delay(10)
            a.next = i
            yield delay(10)
            assert z == ~a
            print(z)
        raise StopSimulation

    return case_inst, stimulus


# signed and unsigned
@pytest.mark.verify_convert
@block
def test_unsigned():
    z = Signal(intbv(0)[8:])
    a = [Signal(intbv(0)[8:]) for i in range(3)]

    @always_comb
    def logic():
        z.next = a[1] + a[2]

    @instance
    def stimulus():
        a[0].next = 2
        a[1].next = 5
        yield delay(10)
        print(z)

    return logic, stimulus
        

@pytest.mark.verify_convert
@block
def test_signed():
    z = Signal(intbv(0, min=-10, max=34))
    a = [Signal(intbv(0, min=-5, max=17)) for i in range(3)]

    @always_comb
    def logic():
        z.next = a[1] + a[2]

    @instance
    def stimulus():
        a[0].next = 2
        a[1].next = -5
        yield delay(10)
        print(z)

    return logic, stimulus


@pytest.mark.verify_convert
@block
def test_mixed():
    z = Signal(intbv(0, min=0, max=34))
    a = [Signal(intbv(0, min=-11, max=17)) for i in range(3)]
    b = [Signal(intbv(0)[5:]) for i in range(3)]

    @always_comb
    def logic():
        z.next = a[1] + b[2]

    @instance
    def stimulus():
        a[0].next = -6
        b[2].next = 15
        yield delay(10)
        print(z)

    return logic, stimulus
        

### error tests

# port in list

@block
def portInList(z, a, b):

    m = [a, b]

    @always_comb
    def logic():
        z.next = m[0] + m[1]

    return logic


def test_portInList():
    z, a, b = [Signal(intbv(0)[8:]) for i in range(3)]

    with pytest.raises(ConversionError) as e:
        portInList(z, a, b).analyze_convert()
    assert e.value.kind == _error.PortInList
       
    
# signal in multiple lists

@block
def sigInMultipleLists():

    z, a, b = [Signal(intbv(0)[8:]) for i in range(3)]

    m1 = [a, b]
    m2 = [a, b]

    @always_comb
    def logic():
        z.next = m1[0] + m2[1]

    return logic

def test_sigInMultipleLists():

    with pytest.raises(ConversionError) as e:
        sigInMultipleLists().analyze_convert()
    assert e.value.kind == _error.SignalInMultipleLists

# list of signals as port
       
@block
def my_register(clk, inp, outp):
    @always(clk.posedge)
    def my_register_impl():
        for index in range(len(inp)):
            outp[index].next = inp[index]
    return my_register_impl

def test_listAsPort():
    count = 3
    clk = Signal(False)
    inp = [Signal(intbv(0)[8:0]) for index in range(count)]
    outp = [Signal(intbv(0)[8:0]) for index in range(count)]
    with pytest.raises(ConversionError) as e:
        inst = conversion.analyze(my_register(clk, inp, outp))
    assert e.value.kind == _error.ListAsPort
