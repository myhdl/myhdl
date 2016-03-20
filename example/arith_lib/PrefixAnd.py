import myhdl
from myhdl import *

from arith_utils import log2ceil
from arith_utils import SLOW, MEDIUM, FAST

def PrefixAnd(width, speed, PI, PO):

    n = width
    m = log2ceil(width)

    def fastPrefix():
        PT = Signal(intbv(0))
        @instance
        def logic():
            while 1:
                yield PI, PT
                PT.next[n:] = PI
                for l in range(1, m+1):
                    for k in range(2**(m-l)):
                        for i in range(2**(l-1)):
                            if (k*2**l + i) < n:
                                PT.next[l*n + k*2**l + i] = \
                                    PT[(l-1)*n + k*2**l + i]
                            if (k*2**l + 2**(l-1) + i) < n:
                                PT.next[l*n + k*2**l + 2**(l-1) + i] = \
                                    PT[(l-1)*n + k*2**l + 2**(l-1) + i] & \
                                    PT[(l-1)*n + k*2**l + 2**(l-1) - 1]
                PO.next = PT[(m+1)*n:m*n]
        return logic

    def slowPrefix():
        PT = Signal(intbv(0))
        @instance
        def logic():
            while 1:
                yield PI, PT
                PT.next[0] = PI[0]
                for i in range(1, n):
                    PT.next[i] = PI[i] & PT[i-1]
                PO.next = PT
        return logic

    if speed == SLOW:
        return slowPrefix()
    elif speed == FAST:
        return fastPrefix()
    else:
        raise NotImplementedError
        
    
