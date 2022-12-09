import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

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
    

def bin2grayBench(width, bin2gray):

    B = Signal(intbv(0)[width:])
    G = Signal(intbv(0)[width:])

    bin2gray_inst = bin2gray(B, G, width)

    n = 2**width

    @instance
    def stimulus():
        for i in range(n):
            B.next = i
            yield delay(10)
            print("%d" % G)

    return stimulus, bin2gray_inst

def testOldVerify():
    try:
        conversion.verify(bin2grayBench, width=8, bin2gray=bin2gray)
    except DeprecationWarning as e:
        pass
    except Exception as e:
        raise e

def testOldAnalyze():
    try:
        conversion.analyze(bin2grayBench, width=8, bin2gray=bin2gray)
    except DeprecationWarning as e:
        pass
    except Exception as e:
        raise e

def testOldToVHDL():
    try:
        toVHDL(bin2grayBench, width=8, bin2gray=bin2gray)
    except DeprecationWarning as e:
        pass
    except Exception as e:
        raise e

def testOldToVerilog():
    try:
        toVerilog(bin2grayBench, width=8, bin2gray=bin2gray)
    except DeprecationWarning as e:
        pass
    except Exception as e:
        raise e
