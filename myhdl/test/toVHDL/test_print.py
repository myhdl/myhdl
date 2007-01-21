from myhdl import *

def PrintBench():

    @instance
    def logic():
        i1 = intbv(0)[8:]
        i2 = intbv(0, min=-10, max=12)
        b = bool(1)
        i1[:] = 10
        print int(i1)
        yield delay(10)
        print "Test"
        yield delay(10)
        print i1
        yield delay(10)
        i2[:] = -7
        print i2
        yield delay(10)
        print int(b)
        yield delay(10)

    return logic

def testPrint():
    assert conversion.verify(PrintBench) == 0
