from myhdl import *
import pytest

def bin2gray_depr(B, G, width):

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

width = 8
B = Signal(intbv(0)[width:])
G = Signal(intbv(0)[width:])

def testOldVerify():
    with pytest.deprecated_call():
        conversion.verify(bin2gray_depr, width, B, G)

def testOldAnalyze():
    with pytest.deprecated_call():
        conversion.analyze(bin2gray_depr, width, B, G)

def testOldToVHDL():
    with pytest.deprecated_call():
        toVHDL(bin2gray_depr, width, B, G)

def testOldToVerilog():
    with pytest.deprecated_call():
        toVerilog(bin2gray_depr, width, B, G)
