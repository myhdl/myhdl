import os
path = os.path
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl.test import verifyConversion

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
    while 1:
        yield left, right
##         Bitand.next = left & right
##         Bitor.next = left | right
##         Bitxor.next = left ^ right
##         if right != 0:
##             FloorDiv.next = left // right
##         if left < 256 and right < 40:
##             LeftShift.next = left << right
##         if right != 0:
##             Modulo.next = left % right
##         Mul.next = left * right
        # Icarus doesn't support ** yet
        #if left < 256 and right < 40:
        #    Pow.next = left ** right
##         Pow.next = 0
##         RightShift.next = left >> right
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


def binaryBench(m, n):

    M = 2**m
    N = 2**n
    P = min(M, N)

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

    def stimulus():
##         for i in range(P):
##             print i
##             left.next = intbv(i)
##             right.next = intbv(i)
##             yield delay(10)
##         for i in range(100):
##             left.next = randrange(M)
##             right.next = randrange(N)
##             yield delay(10)
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
        # raise StopSimulation


    def check():
        while True:
            yield left, right
            yield delay(1)
            # print "%s %s %s %s" % (left, right, Boolor, Boolor_v)
##             self.assertEqual(Bitand, Bitand_v)
##             self.assertEqual(Bitor, Bitor_v)
##             self.assertEqual(Bitxor, Bitxor_v)
##             self.assertEqual(FloorDiv, FloorDiv_v)
##             self.assertEqual(LeftShift, LeftShift_v)
##             self.assertEqual(Modulo, Modulo_v)
##             self.assertEqual(Mul, Mul_v)
##             # self.assertEqual(Pow, Pow_v)
##             self.assertEqual(RightShift, RightShift_v)
##             self.assertEqual(Sub, Sub_v)
##             self.assertEqual(Sum, Sum_v)
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
##             self.assertEqual(EQ, EQ_v)
##             self.assertEqual(NE, NE_v)
##             self.assertEqual(LT, LT_v)
##             self.assertEqual(GT, GT_v)
##             self.assertEqual(LE, LE_v)
##             self.assertEqual(GE, GE_v)
##             self.assertEqual(Booland, Booland_v)
##             self.assertEqual(Boolor, Boolor_v)

    return binops, stimulus(), check()


def testBinary():
    for m, n in ((4, 4,), (5, 3), (2, 6), (8, 7)):
        yield checkBinary, m, n

def checkBinary(m, n):
    assert verifyConversion(binaryBench, m, n) == 0



## def multiOps(
##               Bitand,
##               Bitor,
##               Bitxor,
##               Booland,
##               Boolor,
##               argm, argn, argp):
##     while 1:
##         yield argm, argn, argp
##         Bitand.next = argm & argn & argp
##         Bitor.next = argm | argn | argp
##         Bitxor.next = argm ^ argn ^ argp
##         Booland.next = bool(argm) and bool(argn) and bool(argp)
##         Boolor.next = bool(argm) and bool(argn) and bool(argp)


## def multiOps_v( name,
##                 Bitand,
##                 Bitor,
##                 Bitxor,
##                 Booland,
##                 Boolor,
##                 argm, argn, argp):

##     return setupCosimulation(**locals())

## class TestMultiOps(TestCase):

##     def multiBench(self, m, n, p):

##         M = 2**m
##         N = 2**n
##         P = 2**p

##         argm = Signal(intbv(0)[m:])
##         argn = Signal(intbv(0)[n:])
##         argp = Signal(intbv(0)[p:])
##         Bitand = Signal(intbv(0)[max(m, n, p):])
##         Bitand_v = Signal(intbv(0)[max(m, n, p):])
##         Bitor = Signal(intbv(0)[max(m, n, p):])
##         Bitor_v = Signal(intbv(0)[max(m, n, p):])
##         Bitxor = Signal(intbv(0)[max(m, n, p):])
##         Bitxor_v = Signal(intbv(0)[max(m, n, p):])
##         Booland, Boolor = [Signal(bool()) for i in range(2)]
##         Booland_v, Boolor_v, = [Signal(bool()) for i in range(2)]

##         multiops = toVerilog(multiOps,
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            Booland,
##                            Boolor,
##                            argm, argn, argp)
##         multiops_v = multiOps_v(multiOps.func_name,
##                                 Bitand_v,
##                                 Bitor_v,
##                                 Bitxor_v,
##                                 Booland_v,
##                                 Boolor_v,
##                                 argm, argn, argp)

##         def stimulus():
##             for i in range(min(M, N, P)):
##                 # print i
##                 argm.next = intbv(i)
##                 argn.next = intbv(i)
##                 argp.next = intbv(i)
##                 yield delay(10)
##             for i in range(100):
##                 argm.next = randrange(M)
##                 argn.next = randrange(N)
##                 argp.next = randrange(P)
##                 yield delay(10)
##             for j, k, l in ((0, 0, 0),   (0, 0, P-1), (0, N-1, P-1),
##                             (M-1, 0, 0),  (M-1, 0, P-1), (M-1, N-1, 0),
##                             (0, N-1, 0), (M-1, N-1, P-1)):
##                 argm.next = j
##                 argn.next = k
##                 argp.next = l
##                 yield delay(10)

##         def check():
##             while 1:
##                 yield argm, argn, argp
##                 yield delay(1)
##                 # print "%s %s %s %s %s" % (argm, argn, argp, Bitxor, Bitxor_v)
##                 self.assertEqual(Bitand, Bitand_v)
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
##                 self.assertEqual(Booland, Booland_v)
##                 self.assertEqual(Boolor, Boolor_v)

##         return multiops, multiops_v, stimulus(), check()
    

##     def testMultiOps(self):
##         for m, n, p in ((4, 4, 4,), (5, 3, 2), (3, 4, 6), (3, 7, 4)):
##             sim = self.multiBench(m, n, p)
##             Simulation(sim).run()



## def unaryOps(
##              Not,
##              Invert,
##              UnaryAdd,
##              UnarySub,
##              arg):
##     while 1:
##         yield arg
##         Not.next = not arg
##         Invert.next = ~arg
##         UnaryAdd.next = +arg
##         UnarySub.next = --arg

## def unaryOps_v(name,
##                Not,
##                Invert,
##                UnaryAdd,
##                UnarySub,
##                arg):
##    return setupCosimulation(**locals())



## class TestUnaryOps(TestCase):

##     def unaryBench(self, m):

##         M = 2**m

##         arg = Signal(intbv(0)[m:])
##         Not = Signal(bool(0))
##         Not_v = Signal(bool(0))
##         Invert = Signal(intbv(0)[m:])
##         Invert_v = Signal(intbv(0)[m:])
##         UnaryAdd = Signal(intbv(0)[m:])
##         UnaryAdd_v = Signal(intbv(0)[m:])
##         UnarySub = Signal(intbv(0)[m:])
##         UnarySub_v = Signal(intbv(0)[m:])

##         unaryops = toVerilog(unaryOps,
##                              Not,
##                              Invert,
##                              UnaryAdd,
##                              UnarySub,
##                              arg)
##         unaryops_v = unaryOps_v(unaryOps.func_name,
##                                 Not_v,
##                                 Invert_v,
##                                 UnaryAdd_v,
##                                 UnarySub_v,
##                                 arg)

##         def stimulus():
##             for i in range(M):
##                 arg.next = intbv(i)
##                 yield delay(10)
##             for i in range(100):
##                 arg.next = randrange(M)
##                 yield delay(10)
##             raise StopSimulation

##         def check():
##             while 1:
##                 yield arg
##                 yield delay(1)
##                 self.assertEqual(Not, Not_v)
##                 self.assertEqual(Invert, Invert_v)
##                 self.assertEqual(UnaryAdd, UnaryAdd_v)
##                 self.assertEqual(UnarySub, UnarySub_v)

##         return unaryops, unaryops_v, stimulus(), check()

##     def testUnaryOps(self):
##         for m in (4, 7):
##             sim = self.unaryBench(m)
##             Simulation(sim).run()


## def augmOps(
##               Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
##               LeftShift,
##               Modulo,
##               Mul,
##               RightShift,
##               Sub,
##               Sum,
##               left, right):
##     var = intbv(0)[max(64, len(left) + len(right)):]
##     while 1:
##         yield left, right
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
##         if left < 256 and right < 40:
##             var[:] = left
##             var <<= right
##             LeftShift.next = var
##         if right != 0:
##             var[:] = left
##             var %= right
##             Modulo.next = var
##         var[:] = left
##         var *= right
##         Mul.next = var
##         var[:] = left
##         var >>= right
##         RightShift.next = var
##         if left >= right:
##             var[:] = left
##             var -= right
##             Sub.next = var
##         var[:] = left
##         var += right
##         Sum.next = var


## def augmOps_v(  name,
##                 Bitand,
##                 Bitor,
##                 Bitxor,
##                 FloorDiv,
##                 LeftShift,
##                 Modulo,
##                 Mul,
##                 RightShift,
##                 Sub,
##                 Sum,
##                 left, right):
##     return setupCosimulation(**locals())

## class TestAugmOps(TestCase):

##     def augmBench(self, m, n):

##         M = 2**m
##         N = 2**n

##         left = Signal(intbv(0)[m:])
##         right = Signal(intbv(0)[n:])
##         Bitand = Signal(intbv(0)[max(m, n):])
##         Bitand_v = Signal(intbv(0)[max(m, n):])
##         Bitor = Signal(intbv(0)[max(m, n):])
##         Bitor_v = Signal(intbv(0)[max(m, n):])
##         Bitxor = Signal(intbv(0)[max(m, n):])
##         Bitxor_v = Signal(intbv(0)[max(m, n):])
##         FloorDiv = Signal(intbv(0)[m:])
##         FloorDiv_v = Signal(intbv(0)[m:])
##         LeftShift = Signal(intbv(0)[64:])
##         LeftShift_v = Signal(intbv(0)[64:])
##         Modulo = Signal(intbv(0)[m:])
##         Modulo_v = Signal(intbv(0)[m:])
##         Mul = Signal(intbv(0)[m+n:])
##         Mul_v = Signal(intbv(0)[m+n:])
##         RightShift = Signal(intbv(0)[m:])
##         RightShift_v = Signal(intbv(0)[m:])
##         Sub = Signal(intbv(0)[max(m, n):])
##         Sub_v = Signal(intbv(0)[max(m, n):])
##         Sum = Signal(intbv(0)[max(m, n)+1:])
##         Sum_v = Signal(intbv(0)[max(m, n)+1:])

##         augmops = toVerilog(augmOps,
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
##                            LeftShift,
##                            Modulo,
##                            Mul,
##                            RightShift,
##                            Sub,
##                            Sum,
##                            left, right)
##         augmops_v = augmOps_v( augmOps.func_name,
##                                Bitand_v,
##                                Bitor_v,
##                                Bitxor_v,
##                                FloorDiv_v,
##                                LeftShift_v,
##                                Modulo_v,
##                                Mul_v,
##                                RightShift_v,
##                                Sub_v,
##                                Sum_v,
##                                left, right)

##         def stimulus():
##             for i in range(min(M, N)):
##                 # print i
##                 left.next = intbv(i)
##                 right.next = intbv(i)
##                 yield delay(10)
##             for i in range(100):
##                 left.next = randrange(M)
##                 right.next = randrange(N)
##                 yield delay(10)
##             for j, k in ((0, 0), (0, N-1), (M-1, 0), (M-1, N-1)):
##                 left.next = j
##                 right.next = k
##                 yield delay(10)

##         def check():
##             while 1:
##                 yield left, right
##                 yield delay(1)
##                 # print "%s %s %s %s" % (left, right, Boolor, Boolor_v)
##                 self.assertEqual(Bitand, Bitand_v)
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
##                 self.assertEqual(FloorDiv, FloorDiv_v)
##                 self.assertEqual(LeftShift, LeftShift_v)
##                 self.assertEqual(Modulo, Modulo_v)
##                 self.assertEqual(Mul, Mul_v)
##                 self.assertEqual(RightShift, RightShift_v)
##                 self.assertEqual(Sub, Sub_v)
##                 self.assertEqual(Sum, Sum_v)

##         return augmops, augmops_v, stimulus(), check()
    

##     def testAugmOps(self):
##         for m, n in ((4, 4,), (5, 3), (2, 6), (8, 7)):
##             sim = self.augmBench(m, n)
##             Simulation(sim).run()

