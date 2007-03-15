from myhdl import *

def PrintBench():
    si1 = Signal(intbv(0)[8:])
    si2 = Signal(intbv(0, min=-10, max=12))
    sb = Signal(bool(0))

    @instance
    def logic():
        i1 = intbv(0)[8:]
        i2 = intbv(0, min=-10, max=12)
        b = bool(1)
        i1[:] = 10
        si1.next = 11
        i2[:] = -7
        si2.next = -5
        yield delay(10)
        print i1
        print i2
        print si1
        print si2
        yield delay(10)
        print "This is a test"
        yield delay(10)
        print int(b)
        print int(sb)
        yield delay(10)
        #print "i1 is %s" % i1
        yield delay(10)
        print "%% %s" % i1

    return logic

def testPrint():
    assert conversion.verify(PrintBench) == 0
