from __future__ import generators
from myhdl import Signal, delay, Simulation, intbv, bin

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


