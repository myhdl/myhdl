from __future__ import absolute_import
import os
path = os.path
import random
from random import randrange

from myhdl import *
from myhdl.conversion import verify


NRTESTS = 10

def binaryOps(
    Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
    LeftShift,
    Modulo,
    Mul,
##               Pow,
    RightShift,
    Sub,
    Sum, Sum1, Sum2, Sum3,
    EQ,
    NE,
    LT,
    GT,
    LE,
    GE,
    BoolAnd,
    BoolOr,
    left, right, aBit):

    @instance
    def logic():
        while 1:
            yield left, right, aBit
    ##         Bitand.next = left & right
    ##         Bitor.next = left | right
    ##         Bitxor.next = left ^ right
    ##         if right != 0:
    ##             FloorDiv.next = left // right
            # Keep left shifts smaller than 2** 31 for VHDL's to_integer
            if left < 256 and right < 22 and right >= 0:
                LeftShift.next = left << right
    ##         if right != 0:
    ##             Modulo.next = left % right
            Mul.next = left * right
    ##         # Icarus doesn't support ** yet
    ##         #if left < 256 and right < 22:
    ##         #    Pow.next = left ** right
    ##         Pow.next = 0
    ##         if right >= -0:
    ##            RightShift.next = left >> right
                ## RightShift.next = left
            Sub.next = left - right
            Sum.next = left + right
            Sum1.next = left + right[2:]
            Sum2.next = left + right[1]
            Sum3.next = left + aBit
            EQ.next = left == right
            NE.next = left != right
            LT.next = left < right
            GT.next = left > right
            LE.next = left <= right
            GE.next = left >= right
            BoolAnd.next = bool(left) and bool(right)
            BoolOr.next = bool(left) or bool(right)
    return logic



def binaryBench(Ll, Ml, Lr, Mr):

    seqL = []
    seqR = []
    for i in range(NRTESTS):
        seqL.append(randrange(Ll, Ml))
        seqR.append(randrange(Lr, Mr))
    for j, k in ((Ll, Lr), (Ml-1, Mr-1), (Ll, Mr-1), (Ml-1, Lr)):
        seqL.append(j)
        seqR.append(k)
    seqL = tuple(seqL)
    seqR = tuple(seqR)
        

    aBit = Signal(bool(0))
    left = Signal(intbv(Ll, min=Ll, max=Ml))
    right = Signal(intbv(Lr, min=Lr, max=Mr))
    M = 2**14
    
    Bitand = Signal(intbv(0, min=-2**17, max=2**17))
##        Bitand_v = Signal(intbv(0, min=-2**17, max=2**17))
##         Bitor = Signal(intbv(0)[max(m, n):])
##         Bitor_v = Signal(intbv(0)[max(m, n):])
##         Bitxor = Signal(intbv(0)[max(m, n):])
##         Bitxor_v = Signal(intbv(0)[max(m, n):])
##         FloorDiv = Signal(intbv(0)[m:])
##         FloorDiv_v = Signal(intbv(0)[m:])
    LeftShift = Signal(intbv(0, min=-2**64, max=2**64))
    Modulo = Signal(intbv(0)[M:])
    Mul = Signal(intbv(0, min=-2**17, max=2**17))
##         Pow = Signal(intbv(0)[64:])
    RightShift = Signal(intbv(0, min=-M, max=M))
    Sub, Sub1, Sub2, Sub3 = [Signal(intbv(min=-M, max=M)) for i in range(4)]
    Sum, Sum1, Sum2, Sum3 = [Signal(intbv(min=-M, max=M)) for i in range(4)]
    EQ, NE, LT, GT, LE, GE = [Signal(bool()) for i in range(6)]
    BoolAnd, BoolOr = [Signal(bool()) for i in range(2)]

    binops = binaryOps(
        Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
        LeftShift,
        Modulo,
        Mul,
   ##                            Pow,
        RightShift,
        Sub,
        Sum, Sum1, Sum2, Sum3,
        EQ,
        NE,
        LT,
        GT,
        LE,
        GE,
        BoolAnd,
        BoolOr,
        left, right, aBit)


    @instance
    def stimulus():
        for i in range(len(seqL)):
            left.next = seqL[i]
            right.next = seqR[i]
            yield delay(10)

    @instance
    def check():
        while 1:
            yield left, right
            aBit.next = not aBit
            yield delay(1)
            
                #print "%s %s %s %s" % (left, right, Mul, Mul_v)
                #print "%s %s %s %s" % (left, right, bin(Mul), bin(Mul_v))
                #print "%s %s %s %s" % (left, right, Sum, Sum_v)
                #print "%s %s %s %s" % (left, right, bin(Sum), bin(Sum_v))
##                 print left
##                 print right
##                 print bin(left)
##                 print bin(right)
##                 print bin(Bitand)
##                 print bin(Bitand_v)
##                 print Bitand
##                 print Bitand_v
##                self.assertEqual(Bitand, Bitand_v)
                #w = len(Bitand)
                #self.assertEqual(bin(Bitand, w), bin(Bitand_v,w ))
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
## ##                 self.assertEqual(FloorDiv, FloorDiv_v)
            print LeftShift
            # print Modulo
            print Mul
                # self.assertEqual(Pow, Pow_v)
            print RightShift
            print Sub
            print Sum
            print Sum1
            print Sum2
            print Sum3
            print int(EQ)
            print int(NE)
            print int(LT)
            print int(GT)
            print int(LE)
            print int(GE)
            print int(BoolAnd)
            print int(BoolOr)

    return binops, stimulus, check
    

def checkBinaryOps( Ll, Ml, Lr, Mr):
    assert verify(binaryBench, Ll, Ml, Lr, Mr ) == 0

def testBinaryOps():
    for Ll, Ml, Lr, Mr in (
                            (-254, 236, 0, 4),
                            (-128, 128, -128, 128),
                            (-53, 25, -23, 123),
                            (-23, 145, -66, 12),
                            (23, 34, -34, -16),
                            (-54, -20, 45, 73),
                            (-25, -12, -123, -66),
                           ):
        yield checkBinaryOps, Ll, Ml, Lr, Mr




            
def unaryOps(
             BoolNot,
             Invert,
             UnaryAdd,
             UnarySub,
             arg):
    @instance
    def logic():
        while 1:
            yield arg
            # BoolNot.next = not arg
            Invert.next = ~arg
            # UnaryAdd.next = +arg
            UnarySub.next = --arg
    return logic



            

def unaryBench( m):

    M = 2**m
    seqM = tuple([i for i in range(-M, M)])

    arg = Signal(intbv(0, min=-M, max=+M))
    BoolNot = Signal(bool(0))
    Invert = Signal(intbv(0, min=-M, max=+M))
    UnaryAdd = Signal(intbv(0, min=-M, max=+M))
    UnarySub = Signal(intbv(0, min=-M, max=+M))

    unaryops = unaryOps(
                         BoolNot,
                         Invert,
                         UnaryAdd,
                         UnarySub,
                         arg)

    @instance
    def stimulus():
        for i in range(len(seqM)):
            arg.next = seqM[i]
            yield delay(10)
        raise StopSimulation

    @instance
    def check():
        while 1:
            yield arg
            yield delay(1)
            # print BoolNot
            print Invert
            # print UnaryAdd
            print UnarySub

                             
    return unaryops, stimulus, check


def checkUnaryOps(m):
    assert verify(unaryBench, m) == 0
    

def testUnaryOps():
    for m in (4, 7):
        yield checkUnaryOps, m




def augmOps(
##               Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
              LeftShift,
##               Modulo,
              Mul,
              RightShift,
              Sub,
              Sum,
              left, right):

    M = 2**17
    N = 2**64
    @instance
    def logic():
        var = intbv(0, min=-M, max=+M)
        var2 = intbv(0, min=-N, max=+N)
        while 1:
            yield left, right
    ##         var[:] = left
    ##         var &= right
    ##         Bitand.next = var
    ##         var[:] = left
    ##         var |= right
    ##         Bitor.next = var
    ##         var[:] = left
    ##         var ^= left
    ##         Bitxor.next = var
    ##         if right != 0:
    ##             var[:] = left
    ##             var //= right
    ##             FloorDiv.next = var
            if left < 256 and right < 22 and right >= 0:
                var2[:] = left
                var2 <<= right
                LeftShift.next = var2
    ##         if right != 0:
    ##             var[:] = left
    ##             var %= right
    ##             Modulo.next = var
            var[:] = left
            var *= right
            Mul.next = var

            var[:] = left
            if right >= 0:
                var >>= right
                RightShift.next = var

            var[:] = left
            var -= right
            Sub.next = var
            var[:] = left
            var += right
            Sum.next = var

    return logic



def augmBench( Ll, Ml, Lr, Mr):
    
    M = 2**17
    
    seqL = []
    seqR = []
    for i in range(NRTESTS):
        seqL.append(randrange(Ll, Ml))
        seqR.append(randrange(Lr, Mr))
    for j, k in ((Ll, Lr), (Ml-1, Mr-1), (Ll, Mr-1), (Ml-1, Lr)):
        seqL.append(j)
        seqR.append(k)
    seqL = tuple(seqL)
    seqR = tuple(seqR)
    
    left = Signal(intbv(Ll, min=Ll, max=Ml))
    right = Signal(intbv(Lr, min=Lr, max=Mr))

        
##         Bitand = Signal(intbv(0)[max(m, n):])
##         Bitor = Signal(intbv(0)[max(m, n):])
##         Bitxor = Signal(intbv(0)[max(m, n):])
        
##         FloorDiv = Signal(intbv(0)[m:])
    LeftShift = Signal(intbv(0, min=-2**64, max=2**64))
##         Modulo = Signal(intbv(0)[m:])
        
    Mul = Signal(intbv(0, min=-M, max=+M))
        
    RightShift = Signal(intbv(0, min=-M, max=+M))

    Sub = Signal(intbv(0, min=-M, max=+M))
    Sum = Signal(intbv(0, min=-M, max=+M))

    augmops = augmOps(
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
        LeftShift,
##                            Modulo,
        Mul,
        RightShift,
        Sub,
        Sum,
        left, right)

    @instance
    def stimulus():
        for i in range(len(seqL)):
            left.next = seqL[i]
            right.next = seqR[i]
            yield delay(10)
    @instance
    def check():
        while 1:
            yield left, right
            yield delay(1)
                # print "%s %s %s %s" % (left, right, Or, Or_v)
##                 self.assertEqual(Bitand, Bitand_v)
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
##                 self.assertEqual(FloorDiv, FloorDiv_v)
            print LeftShift
##                 self.assertEqual(Modulo, Modulo_v)
            print Mul
            print RightShift
            print Sub
            print Sum

    return augmops,  stimulus, check
    
            
def checkAugmOps( Ll, Ml, Lr, Mr):
    assert verify(augmBench, Ll, Ml, Lr, Mr) == 0

def testAugmOps():
    for Ll, Ml, Lr, Mr in (
                            (-254, 236, 0, 4),
                            (-128, 128, -128, 128),
                            (-53, 25, -23, 123),
                            (-23, 145, -66, 12),
                            (23, 34, -34, -16),
                            (-54, -20, 45, 73),
                            (-25, -12, -123, -66),
                           ):
        yield checkAugmOps, Ll, Ml, Lr, Mr


def expressions(a, b, clk):

    c = Signal(intbv(0, min=0, max=47))
    e = Signal(bool())

    @instance
    def logic():

        d = intbv(0, min=-23, max=43)
        d[:] = -17

        c.next = 5
        yield clk.posedge
        a.next = c + 1
        b.next = c + 1
        yield clk.posedge
        a.next = c + -10
        b.next = c + -1
        yield clk.posedge
        a.next = c < -10
        b.next = c < -1
        yield clk.posedge
        a.next = d + c
        b.next = d >= c
        yield clk.posedge
##         a.next = d & c
##         b.next = c + (d & c)
        yield clk.posedge
        a.next = d + -c
        b.next = c + (-d)
        yield clk.posedge
        a.next = -d
        yield clk.posedge
        a.next = -c
        yield clk.posedge
        c.next = 46
        yield clk.posedge
        a.next = ~d + 1
        b.next = ~c + 1
        yield clk.posedge
        a.next = ~c + 1
        b.next = ~d + 1
        
        yield clk.posedge
        raise StopSimulation

    return logic
        


def expressionsBench():

    a = Signal(intbv(0, min=-34, max=47))
    b = Signal(intbv(0, min=0, max=47))
    clk = Signal(bool())

    expr = expressions(a, b, clk)

    @instance
    def check():
        while 1:
            yield clk.posedge
            yield delay(1)
            print int(a)
            print int(b)

    @instance
    def clkgen():
        while True:
            yield delay(10)
            clk.next = not clk

    return expr, check, clkgen


def testExpressions():
    assert verify(expressionsBench) == 0




