import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

t_State = enum("START", "RUN", "STOP")

@block
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
        print('')
        print(i1)
        print(i2)
        print("%d %d" % (i1, i2))
        print(si1)
        print(si2)

        yield delay(10)
        print("This is a test")

        yield delay(10)
        print(int(b))
        print(int(sb))

        yield delay(10)
        print("i1 is %s" % i1)

        yield delay(10)
        print("i1 is %s, i2 is %s" % (i1, i2))
        print("i1 %s i2 %s b %s si1 %s si2 %s" % (i1, i2, b, si1, si2))
        print("i1 %d i2 %d b %d si1 %d si2 %d" % (i1, i2, b, si1, si2))
        print(b)
        #print "%% %s" % i1

        yield delay(10)
        print(state)
        print("the state is %s" % state)
        print("the state is %s" % (state,))
        print("i1 is %s and the state is %s" % (i1, state))

        # ord test
        yield delay(10)
        print(ord('y'))
        print(ord('2'))

        # signed
        yield delay(10)
        print(i1.signed())
        print(i2.signed())
        print(si1.signed())
        print(si2.signed())

    return logic

def testPrint():
    assert PrintBench().verify_convert() == 0

@block
def PrintLongVectorsBench():
    N84 = 84
    M84 = 2**N84-1
    N85 = 85
    M85 = 2**N85-1
    N86 = 86
    M86 = 2**N86-1
    N87 = 87
    M87 = 2**N87-1

    si1 = Signal(intbv(0)[N87:])
    si2 = Signal(intbv(0, min=-M85, max=M86))

    @instance
    def logic():
        i1 = intbv(0)[N85:]
        i2 = intbv(0, min=-M86, max=M85)
        si1.next = 0
        si2.next = 0
        yield delay(10)
        print("%s %s %s %s" % (i1, i2, si1, si2))
        i1[:] = M84
        i2[:] = -1
        si1.next = M85
        si2.next = -1
        yield delay(10)
        print("%s %s %s %s" % (i1, i2, si1, si2))
        i1[:] = 596854
        i2[:] = -4954502
        si1.next = 232434
        si2.next = -3434355
        yield delay(10)
        print("%s %s %s %s" % (i1, i2, si1, si2))

    return logic

def testPrintLongVectors():
    assert PrintLongVectorsBench().verify_convert() == 0

# format string errors and unsupported features

@block
def PrintError1():
     @instance
     def logic():
         i1 = intbv(12)[8:]
         yield delay(10)
         print("floating point %f end" % i1)
     return logic

def testPrintError1():
    try:
        PrintError1().verify_convert()
    except ConversionError as e:
        assert e.kind == _error.UnsupportedFormatString
    else:
        assert False

@block
def PrintError2():
     @instance
     def logic():
         i1 = intbv(12)[8:]
         yield delay(10)
         print("begin %s %s end" % i1)
     return logic

def testPrintError2():
    try:
        PrintError2().verify_convert()
    except ConversionError as e:
        assert e.kind == _error.FormatString
    else:
        assert False

@block
def PrintError3():
     @instance
     def logic():
         i1 = intbv(12)[8:]
         i2 = intbv(13)[8:]
         yield delay(10)
         print("begin %s end" % (i1, i2))
     return logic

def testPrintError3():
    try:
        PrintError3().verify_convert()
    except ConversionError as e:
        assert e.kind == _error.FormatString
    else:
        assert False

@block
def PrintError4():
     @instance
     def logic():
         i1 = intbv(12)[8:]
         yield delay(10)
         print("%10s" % i1)
     return logic

def testPrintError4():
    try:
        PrintError4().verify_convert()
    except ConversionError as e:
        assert e.kind == _error.UnsupportedFormatString
    else:
        assert False

@block
def PrintError5():
     @instance
     def logic():
         i1 = intbv(12)[8:]
         yield delay(10)
         print("%-10s" % i1)
     return logic

def testPrintError5():
    try:
        PrintError5().verify_convert()
    except ConversionError as e:
        assert e.kind == _error.UnsupportedFormatString
    else:
        assert False
