import myhdl
from myhdl import *
from arith_utils import BEHAVIOR
from PrefixAnd import PrefixAnd

def LeadZeroDet(width, speed, A, Z, architecture=BEHAVIOR):
    
    """ Set output bit to 1 at first non-zero MSB bit in input

    width -- bit width
    speed -- SLOW, MEDIUM, or FAST performance
    A -- input
    Z -- output
    architecture - BEHAVIOR or STRUCTURE

    """

    @instance
    def Behavioral():
        while 1:
            yield A
            zv = intbv(0)
            for i in downrange(width):
                if A[i] == 1:
                    zv[i] = 1
                    break
            Z.next = zv

    def Structural():
        PI = Signal(intbv(0))
        PO = Signal(intbv(0))
        PIT = Signal(intbv(0))
        POT = Signal(intbv(0))
        prefix = PrefixAnd(width, speed, PIT, POT)
        @instance
        def logic():
            while 1:
                yield PI, POT, PO, A
                PI.next = ~A
                for i in downrange(width):
                    PIT.next[i] = PI[width-i-1]
                    PO.next[i] = POT[width-i-1]
                Z.next[width-1] = A[width-1]
                Z.next[width-1:] = PO[width:1] & A[width-1:]
        return [prefix, logic]

    if architecture == BEHAVIOR:
        return Behavioral
    else:
        return Structural()
                
                    

        

