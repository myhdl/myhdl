from __future__ import generators
from myhdl import Signal, delay, Simulation, intbv, bin

def bin2gray(width, B, G):
    """ Gray encoder.

    width -- bit width
    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    """
    while 1:
        yield B
        for i in range(width):
            G.next[i] = B[i+1] ^ B[i]

def testBench(width):
    
    B = Signal(intbv(0))
    G = Signal(intbv(0))
    
    dut = bin2gray(width, B, G)

    def stimulus():
        for i in range(2**width):
            B.next = intbv(i)
            yield delay(10)
            print "B: " + bin(B, width) + "| G: " + bin(G, width)

    return (dut, stimulus())

if __name__ == '__main__':
    Simulation(testBench(width=3)).run()
    

