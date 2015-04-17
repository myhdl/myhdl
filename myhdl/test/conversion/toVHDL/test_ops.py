from __future__ import absolute_import
import os
path = os.path
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl.conversion import verify

NRTESTS = 10

def binaryOps(
              Bitand,
              Bitor,
              Bitxor,
              FloorDiv,
              LeftShift,
              Modulo,
              Mul,
              Pow,
              RightShift,
              Sub,
              Sum,
              EQ,
              NE,
              LT,
              GT,
              LE,
              GE,
              Booland,
              Boolor,
              left, right):

    @instance
    def logic():
        while 1:
            yield left, right
            Bitand.next = left & right
            Bitor.next = left | right
            Bitxor.next = left ^ right
            if right != 0:
                FloorDiv.next = left // right
    ##         if left < 256 and right < 40:
            if left < 256 and right < 26: # fails in ghdl for > 26
                LeftShift.next = left << right
            if right != 0:
                Modulo.next = left % right
            Mul.next = left * right
            # Icarus doesn't support ** yet
            #if left < 256 and right < 40:
            #    Pow.next = left ** right
    ##         Pow.next = 0
            RightShift.next = left >> right
            if left >= right:
                Sub.next = left - right
            Sum.next = left + right
            EQ.next = left == right
            NE.next = left != right
            LT.next = left < right
            GT.next = left > right
            LE.next = left <= right
            GE.next = left >= right
            Booland.next = bool(left) and bool(right)
            Boolor.next = bool(left) or bool(right)
    return logic


def binaryBench(m, n):

    M = 2**m
    N = 2**n
    P = min(M, N)
    seqP = tuple(range(P))
    seqM = tuple([randrange(M) for i in range(NRTESTS)])
    seqN = tuple([randrange(N) for i in range(NRTESTS)])

    left = Signal(intbv(0)[m:])
    right = Signal(intbv(0)[n:])
    Bitand = Signal(intbv(0)[max(m, n):])
    Bitor = Signal(intbv(0)[max(m, n):])
    Bitxor = Signal(intbv(0)[max(m, n):])
    FloorDiv = Signal(intbv(0)[m:])
    LeftShift = Signal(intbv(0)[64:])
    Modulo = Signal(intbv(0)[m:])
    Mul = Signal(intbv(0)[m+n:])
    Pow = Signal(intbv(0)[64:])
    RightShift = Signal(intbv(0)[m:])
    Sub = Signal(intbv(0)[max(m, n):])
    Sum = Signal(intbv(0)[max(m, n)+1:])
    EQ, NE, LT, GT, LE, GE = [Signal(bool()) for i in range(6)]
    Booland, Boolor = [Signal(bool()) for i in range(2)]

    binops = binaryOps(Bitand,
                       Bitor,
                       Bitxor,
                       FloorDiv,
                       LeftShift,
                       Modulo,
                       Mul,
                       Pow,
                       RightShift,
                       Sub,
                       Sum,
                       EQ,
                       NE,
                       LT,
                       GT,
                       LE,
                       GE,
                       Booland,
                       Boolor,
                       left, right)

    @instance
    def stimulus():
        left.next = 1
        right.next = 1
        yield delay(10)
        left.next = 0
        right.next = 0
        yield delay(10)
        left.next = 0
        right.next = N-1
        yield delay(10)
        left.next = M-1
        right.next = 0
        yield delay(10)
        left.next = M-1
        right.next = N-1
        for i in range(len(seqP)):
            left.next = seqP[i]
            right.next = seqP[i]
            yield delay(10)
        for i in range(NRTESTS):
            left.next = seqM[i]
            right.next = seqN[i]
            yield delay(10)
        # raise StopSimulation


    @instance
    def check():
        while True:
            yield left, right
            yield delay(1)

            print Bitand
            print Bitor
            print Bitxor
            print FloorDiv
            print LeftShift

            # print Pow, Pow_v

            print Modulo
            print RightShift
            print Mul
            print Sub
            print Sum
            print int(EQ)
            print int(NE)
            print int(LT)
            print int(GT)
            print int(LE)
            print int(GE)
            print int(Booland)
            print int(Boolor)

    return binops, stimulus, check

def checkBinary(m, n):
    assert verify(binaryBench, m, n) == 0

def testBinary():
    for m, n in ((4, 4,), (5, 3), (2, 6), (8, 7)):
    # for m, n in ((2, 6),):
        yield checkBinary, m, n




def multiOps(
              Bitand,
              Bitor,
              Bitxor,
              Booland,
              Boolor,
              argm, argn, argp):
    @instance
    def logic():
        while 1:
            yield argm, argn, argp
            Bitand.next = argm & argn & argp
            Bitor.next = argm | argn | argp
            Bitxor.next = argm ^ argn ^ argp
            Booland.next = bool(argm) and bool(argn) and bool(argp)
            Boolor.next = bool(argm) and bool(argn) and bool(argp)
    return logic



def multiBench(m, n, p):

    M = 2**m
    N = 2**n
    P = 2**p

    Q = min(M, N, P)
    seqQ = tuple(range(1, Q))
    seqM = tuple([randrange(M) for i in range(NRTESTS)])
    seqN = tuple([randrange(N) for i in range(NRTESTS)])
    seqP = tuple([randrange(P) for i in range(NRTESTS)])

    argm = Signal(intbv(0)[m:])
    argn = Signal(intbv(0)[n:])
    argp = Signal(intbv(0)[p:])
    Bitand = Signal(intbv(0)[max(m, n, p):])
    Bitor = Signal(intbv(0)[max(m, n, p):])
    Bitxor = Signal(intbv(0)[max(m, n, p):])
    Booland, Boolor = [Signal(bool()) for i in range(2)]

    multiops = multiOps(Bitand,
                        Bitor,
                        Bitxor,
                        Booland,
                        Boolor,
                        argm, argn, argp)

    @instance
    def stimulus():
        for i in range(len(seqQ)):
            argm.next = seqQ[i]
            argn.next = seqQ[i]
            argp.next = seqQ[i]
            yield delay(10)
        for i in range(NRTESTS):
            argm.next = seqM[i]
            argn.next = seqN[i]
            argp.next = seqP[i]
            yield delay(10)
##         for j, k, l in ((0, 0, 0),   (0, 0, P-1), (0, N-1, P-1),
##                         (M-1, 0, 0),  (M-1, 0, P-1), (M-1, N-1, 0),
##                         (0, N-1, 0), (M-1, N-1, P-1)):
##             argm.next = j
##             argn.next = k
##             argp.next = l
##             yield delay(10)

    @instance
    def check():
        while 1:
            yield argm, argn, argp
            yield delay(1)

            print Bitand
            print Bitor
            print Bitxor
            print int(Booland)
            print int(Boolor)

    return multiops, stimulus, check

def checkMultiOps(m, n, p):
    assert verify(multiBench, m, n, p) == 0

def testMultiOps():
    for m, n, p in ((4, 4, 4,), (5, 3, 2), (3, 4, 6), (3, 7, 4)):
        yield checkMultiOps, m, n, p


def unaryOps(
             Not_kw,
             Invert,
             UnaryAdd,
             UnarySub,
             arg):
    @instance
    def logic():
        while 1:
            yield arg
            Not_kw.next = not arg
            Invert.next = ~arg
            # unary operators not supported ?
            #UnaryAdd.next = +arg
            # UnarySub.next = --arg
    return logic

def unaryBench(m):

    M = 2**m
    seqM = tuple([randrange(M) for i in range(NRTESTS)])

    arg = Signal(intbv(0)[m:])
    Not_kw = Signal(bool(0))
    Invert = Signal(intbv(0)[m:])
    UnaryAdd = Signal(intbv(0)[m:])
    UnarySub = Signal(intbv(0)[m:])

    unaryops = unaryOps(Not_kw,
                        Invert,
                        UnaryAdd,
                        UnarySub,
                        arg)

    @instance
    def stimulus():
        for i in range(NRTESTS):
            arg.next = seqM[i]
            yield delay(10)
        raise StopSimulation

    @instance
    def check():
        while 1:
            yield arg
            yield delay(1)
            print int(Not_kw)
            print Invert
            # check unary operator support in vhdl
            # print UnaryAdd
            # print UnarySub

    return unaryops, stimulus, check

def checkUnaryOps(m):
    assert verify(unaryBench, m) == 0
    
def testUnaryOps():
    for m in (4, 7):
        yield checkUnaryOps, m


def augmOps(  Bitand,
              Bitor,
              Bitxor,
              FloorDiv,
              LeftShift,
              Modulo,
              Mul,
              RightShift,
              Sub,
              Sum,
              left, right):
    @instance
    def logic():
        # var = intbv(0)[min(64, len(left) + len(right)):]
        var = intbv(0)[len(left) + len(right):]
        var2 = intbv(0)[64:]
        while True:
            yield left, right
            var[:] = left
            var &= right
            Bitand.next = var
            var[:] = left
            var |= right
            Bitor.next = var
            var[:] = left
            var ^= left
            Bitxor.next = var
            if right != 0:
                var[:] = left
                var //= right
                FloorDiv.next = var
            if left >= right:
                var[:] = left
                var -= right
                Sub.next = var
            var[:] = left
            var += right
            Sum.next = var
            if left < 256 and right < 26:
                var2[:] = left
                var2 <<= right
                LeftShift.next = var2
            if right != 0:
                var[:] = left
                var %= right
                Modulo.next = var
            var[:] = left
            var *= right
            Mul.next = var
            var[:] = left
            var >>= right
            RightShift.next = var
    return logic


        


def augmBench(m, n):

    M = 2**m
    N = 2**n
    
    seqM = tuple([randrange(M) for i in range(NRTESTS)])
    seqN = tuple([randrange(N) for i in range(NRTESTS)])

    left = Signal(intbv(0)[m:])
    right = Signal(intbv(0)[n:])
    Bitand = Signal(intbv(0)[max(m, n):])
    Bitor = Signal(intbv(0)[max(m, n):])
    Bitxor = Signal(intbv(0)[max(m, n):])
    FloorDiv = Signal(intbv(0)[m:])
    LeftShift = Signal(intbv(0)[64:])
    Modulo = Signal(intbv(0)[m:])
    Mul = Signal(intbv(0)[m+n:])
    RightShift = Signal(intbv(0)[m:])
    Sub = Signal(intbv(0)[max(m, n):])
    Sum = Signal(intbv(0)[max(m, n)+1:])

    augmops = augmOps( Bitand,
                       Bitor,
                       Bitxor,
                       FloorDiv,
                       LeftShift,
                       Modulo,
                       Mul,
                       RightShift,
                       Sub,
                       Sum,
                       left, right)

    @instance
    def stimulus():
        left.next = 1
        right.next = 1
        yield delay(10)
        left.next = 0
        right.next = 0
        yield delay(10)
        left.next = 0
        right.next = N-1
        yield delay(10)
        left.next = M-1
        right.next = 0
        yield delay(10)
        left.next = M-1
        right.next = N-1
        for i in range(NRTESTS):
            left.next = seqM[i]
            right.next = seqN[i]
            yield delay(10)
            

    @instance
    def check():
        while True:
            yield left, right
            yield delay(1)
            print Bitand
            print Bitor
            print Bitxor
            print Sub
            print Sum
            print FloorDiv
            print LeftShift
            print Modulo
            print Mul
            print RightShift
            
    return augmops, stimulus, check


def checkAugmOps(m, n):
    assert verify(augmBench, m, n) == 0

def testAugmOps():
    for m, n in ((4, 4,), (5, 3), (2, 6), (8, 7)):
        yield checkAugmOps, m, n

