import myhdl
from myhdl import *
from arith_utils import BEHAVIOR
from PrefixAnd import PrefixAnd

def Dec(width, speed, A, Z, architecture=BEHAVIOR):
    
    """ Decrementer module.

    width -- bitwidth of input and output
    speed -- SLOW, MEDIUM, or FAST performance
    A -- input
    Z -- output
    architecture -- BEHAVIOR or STRUCTURE architecture selection

    """

    @instance
    def Behavioral():
        while 1:
            yield A
            Z.next = A - 1

    def Structural():
        AI = Signal(intbv(0))
        PO = Signal(intbv(0))
        prefix = PrefixAnd(width, speed, AI, PO)
        @instance
        def logic():
            while 1:
                yield A, PO
                AI.next = ~A
                Z.next = A ^ concat(PO[width-1:], '1')
        return [prefix, logic]

    if architecture == BEHAVIOR:
        return Behavioral
    else:
        return Structural()
        
        
