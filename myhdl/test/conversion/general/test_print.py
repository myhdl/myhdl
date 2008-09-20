from myhdl import *
from myhdl import ConversionError

t_State = enum("START", "RUN", "STOP")

def PrintBench():
    si1 = Signal(intbv(0)[8:])
    si2 = Signal(intbv(0, min=-10, max=12))
    sb = Signal(bool(0))

    @instance
    def logic():
        i1 = intbv(0)[8:]
        i2 = intbv(0, min=-10, max=12)
        b = bool(1)
        state = t_State.START
        i1[:] = 10
        si1.next = 11
        i2[:] = -7
        si2.next = -5
        yield delay(10)
        print
        print i1
        print i2
        print i1, i2
        print si1
        print si2
        yield delay(10)
        print "This is a test"
        yield delay(10)
        print int(b)
        print int(sb)
        yield delay(10)
        print "i1 is %s" % i1
        print "i1 is %10s" % i1
#        print "i1 is %-10s" % i1
        yield delay(10)
        print "i1 is %s, i2 is %s" % (i1, i2)
#        print "i1 is %-9s, i2 is %9s" % (i1, i2)
##         print "i1 is %5s, i2 is %-5s" % (i1, i2)
##         print "i1 is %1s, i2 is %-1s" % (i1, i2)
##         yield delay(10)
        print "i1 %s i2 %s b %s si1 %s si2 %s" % (i1, i2, b, si1, si2)
        print "i1 %d i2 %d b %d si1 %d si2 %d" % (i1, i2, b, si1, si2)
        print b
        print "%% %s" % i1
        yield delay(10)
        
        print state
##         print "the state is %s" % state
##         print "the state is %s" % (state,)
##         print "i1 is %s and the state is %s" % (i1, state)

        yield delay(10)
        # ord test
        print ord('y')
        print ord('2')

    return logic

def testPrint():
    assert conversion.verify(PrintBench) == 0

## def PrintError1():
##      @instance
##      def logic():
##          i1 = intbv(12)[8:]
##          yield delay(10)
##          print "floating point %f end" % i1
##      return logic

## def testPrintError1():
##     try:
##         conversion.verify(PrintError1)
##     except ConversionError, e:
##         pass
##     else:
##         assert False
        
## def PrintError2():
##      @instance
##      def logic():
##          i1 = intbv(12)[8:]
##          yield delay(10)
##          print "begin %s %s end" % i1
##      return logic

## def testPrintError2():
##     try:
##         conversion.verify(PrintError2)
##     except ConversionError, e:
##         pass
##     else:
##         assert False
       
## def PrintError3():
##      @instance
##      def logic():
##          i1 = intbv(12)[8:]
##          i2 = intbv(13)[8:]
##          yield delay(10)
##          print "begin %s end" % (i1, i2)
##      return logic

## def testPrintError3():
##     try:
##         conversion.verify(PrintError3)
##     except ConversionError, e:
##         pass
##     else:
##         assert False
       
