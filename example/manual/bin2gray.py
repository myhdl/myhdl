from __future__ import generators
from myhdl import Signal, delay, Simulation, intbv, bin, traceSignals

def bin2gray(B, G, width):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """
    while 1:
        yield B
        for i in range(width):
            G.next[i] = B[i+1] ^ B[i]

def testBench(width):
    
    B = Signal(intbv(0))
    G = Signal(intbv(0))
    
    dut = traceSignals(bin2gray, B, G, width)

    def stimulus():
        for i in range(2**width):
            B.next = intbv(i)
            yield delay(10)
            print "B: " + bin(B, width) + "| G: " + bin(G, width)

    return (dut, stimulus())

def main():
    Simulation(testBench(width=3)).run()
    

if __name__ == '__main__':
    main()
    

