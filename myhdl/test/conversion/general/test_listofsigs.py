from myhdl import *


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
            
    
def test_intbv2list():
    assert conversion.verify(intbv2list) == 0

def inv(z, a):
    @always_comb
    def logic():
        z.next = not a
    return logic
    
def processlist():
    """Extract list from intbv, do some processing, reassemble."""
    
    N = 8
    M= 2**N
    a = Signal(intbv(0)[N:])
    b = [Signal(bool(0)) for i in range(len(a))]
    c = [Signal(bool(0)) for i in range(len(a))]
    z = Signal(intbv(0)[N:])

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

    @instance
    def stimulus():
        for i in range(M):
            a.next = i
            yield delay(10)
            assert z == ~a
            print z
        raise StopSimulation

    return extract, inst, assemble, stimulus
            
    
## def test_processlist():
##     # Simulation(processlist()).run()
##     assert conversion.verify(processlist) == 0



        

    
