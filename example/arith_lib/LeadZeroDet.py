from __future__ import generators
from myhdl import Signal, intbv, downrange
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

    def Behavioral():
        while 1:
            yield A
            zv = intbv(0)
            for i in downrange(width):
                if A.val[i] == 1:
                    zv[i] = 1
                    break
            Z.next = zv

    def Structural():
        PI = Signal(intbv())
        PO = Signal(intbv())
        PIT = Signal(intbv())
        POT = Signal(intbv())
        prefix = PrefixAnd(width, speed, PIT, POT)
        def logic():
            while 1:
                yield PI, POT, PO, A
                PI.next = ~A.val
                for i in downrange(width):
                    PIT.next[i] = PI.val[width-i-1]
                    PO.next[i] = POT.val[width-i-1]
                Z.next[width-1] = A.val[width-1]
                Z.next[width-1:] = PO.val[width:1] & A.val[width-1:]
        return [prefix, logic()]

    if architecture == BEHAVIOR:
        return Behavioral()
    else:
        return Structural()
                
                    

        

