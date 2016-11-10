from __future__ import absolute_import
import os
path = os.path

import pytest

from myhdl import block, Signal, intbv, delay, instance, always_comb

@block
def bin2gray2(B, G, width):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """
    @instance
    def logic():
        Bext = intbv(0)[width+1:]
        while 1:
            yield B
            Bext[:] = B
            for i in range(width):
                G.next[i] = Bext[i+1] ^ Bext[i]
    return logic

@block
def bin2gray(B, G, width):

    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width

    """

    @always_comb
    def logic():
        Bext = intbv(0)[width+1:]
        Bext[:] = B
        for i in range(width):
            G.next[i] = Bext[i+1] ^ Bext[i]

    return logic


@pytest.mark.parametrize('width, bin2gray', [
    (8, bin2gray),
    (8, bin2gray2)
])
@pytest.mark.verify_convert
@block
def test_bin2gray(width, bin2gray):

    B = Signal(intbv(0)[width:])
    G = Signal(intbv(0)[width:])

    bin2gray_inst = bin2gray(B, G, width)

    n = 2**width

    @instance
    def stimulus():
        for i in range(n):
            B.next = i
            yield delay(10)
            #print "B: " + bin(B, width) + "| G_v: " + bin(G_v, width)
            #print bin(G, width)
            #print bin(G_v, width)
            print("%d" % G)

    return stimulus, bin2gray_inst
