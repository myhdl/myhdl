from __future__ import generators
from myhdl import Signal, delay, Simulation, intbv

def bin2gray(width, B, G):
    while 1:
        yield B
        for i in range(width):
            G.next[i] = B.val[i+1] ^ B.val[i]


def test():
    
    width = 8
    B = Signal(intbv(0))
    G = Signal(intbv(0))
    
    dut = bin2gray(width, B, G)

    def stimulus():
        for i in range(2**width):
            B.next = intbv(i)
            yield delay(10)
            print hex(G.val)

    return (dut, stimulus())

Simulation(test()).run()
    

            
