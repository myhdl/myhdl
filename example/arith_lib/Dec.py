from __future__ import generators
from myhdl import Signal, intbv, concat
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

    def Behavioral():
        while 1:
            yield A
            Z.next = A - 1

    def Structural():
        AI = Signal(intbv())
        PO = Signal(intbv())
        prefix = PrefixAnd(width, speed, AI, PO)
        def logic():
            while 1:
                yield A, PO
                AI.next = ~A
                Z.next = A ^ concat(PO[width-1:], '1')
        return [prefix, logic()]

    if architecture == BEHAVIOR:
        return Behavioral()
    else:
        return Structural()
        
        
