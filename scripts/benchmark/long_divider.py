from __future__ import absolute_import
import myhdl
from myhdl import *

def long_divider(
            quotient,
            ready,
            dividend,
            divisor,
            start,
            clock,
            reset
            ):
    

    M = len(dividend)
    N = len(divisor)
    Q = len(quotient)
    
    assert M-N == Q
    
    st = enum("WAIT_START", "CALC")
    
    @instance
    def proc():
        state = st.WAIT_START
        div = intbv(0)[N+1:]
        divbits = intbv(0)[Q-1:]
        quot = intbv(0)[Q:]
        count = intbv(0, min=0, max=Q)
        while True:
            yield clock.posedge, reset.posedge
            if reset == 1:
                quotient.next = 0
                ready.next = 0
                state = st.WAIT_START
                div[:] = 0
                divbits[:] = 0
                quot[:] = 0
            else:
                if state == st.WAIT_START:
                    if start:
                        state = st.CALC
                        ready.next = 0
                        quot[:] = 0
                        div[N+1:] = dividend[M:Q-1]
                        divbits[:] = dividend[Q-1:]
                        count[:] = 0
                        
                elif state == st.CALC:
                    quot[Q:1] = quot[Q-1:]
                    if div >= divisor:
                        quot[0] = 1
                        div -= divisor
                    else:
                        quot[0] = 0
                    
                    if count == Q-1:
                        ready.next = 1
                        state = st.WAIT_START
                    else:
                        div[N+1:1] = div[N:]
                        div[0] = divbits[Q-2]
                        divbits[Q-1:1] = divbits[Q-2:]
                        count += 1
                        
            quotient.next = quot

    return proc


    
if __name__ == '__main__':
    quotient = Signal(intbv(0)[22:])
    ready = Signal(bool())
    dividend = Signal(intbv(0)[38:])
    divisor = Signal(intbv(0)[16:])
    start = Signal(bool())
    clock = Signal(bool())
    reset = Signal(bool())
    
    toVHDL(long_divider,
           quotient,
           ready,
           dividend,
           divisor,
           start,
           clock,
           reset
           )
