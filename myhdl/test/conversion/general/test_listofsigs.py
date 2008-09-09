from myhdl import *


### A first case that already worked with 5.0 list of signal constraints ###

def intbv2list():
    """Conversion between intbv and list of boolean signals."""
    
    N = 8
    M= 2**N
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
            print a
        raise StopSimulation

    return extract, assemble, stimulus

# test

def test_intbv2list():
    assert conversion.verify(intbv2list) == 0
            
    
### A number of cases with relaxed constraints, for various decorator types ###

def inv1(z, a):
    @always(a)
    def logic():
        z.next = not a
    return logic

def inv2(z, a):
    @always_comb
    def logic():
        z.next = not a
    return logic


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



def processlist(case, inv):
    """Extract list from intbv, do some processing, reassemble."""
    
    N = 8
    M = 2**N
    a = Signal(intbv(1)[N:])
    b = [Signal(bool(1)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    z = Signal(intbv(0)[N:])

    case_inst = case(z, a, inv)

    @instance
    def stimulus():
        for i in range(M):
            yield delay(10)
            a.next = i
            yield delay(10)
            assert z == ~a
            print z
        raise StopSimulation

    return case_inst, stimulus


# tests
    
def test_processlist11():
    assert conversion.verify(processlist, case1, inv1) == 0
    
def test_processlist12():
    assert conversion.verify(processlist, case1, inv2) == 0
    
def test_processlist22():
    assert conversion.verify(processlist, case2, inv2) == 0



        

    
