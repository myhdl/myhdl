from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *

from util import setupCosimulation


def binaryOps(
##                 Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
                 LeftShift,
##               Mod,
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
                 And,
                 Or,
                 left, right, bit):

    @instance
    def logic():
        while 1:
            yield left, right
    ##        Bitand.next = left & right
    ##         Bitor.next = left | right
    ##         Bitxor.next = left ^ right
    ##         if right != 0:
    ##             FloorDiv.next = left // right
            if left < 256 and right < 40  and right >= 0:
                LeftShift.next = left << right
    ##         if right != 0:
    ##             Mod.next = left % right
            Mul.next = left * right
    ##         # Icarus doesn't support ** yet
    ##         #if left < 256 and right < 40:
    ##         #    Pow.next = left ** right
    ##         Pow.next = 0
            if right >= -0:
               RightShift.next = left >> right
                ## RightShift.next = left
            Sub.next = left - right
            Sum.next = left + right
            Sum1.next = left + right[2:]
            Sum2.next = left + right[1]
            Sum3.next = left + bit
            EQ.next = left == right
            NE.next = left != right
            LT.next = left < right
            GT.next = left > right
            LE.next = left <= right
            GE.next = left >= right
            And.next = bool(left) and bool(right)
            Or.next = bool(left) or bool(right)

    return logic


def binaryOps_v(name,
##                Bitand,
##                 Bitor,
##                 Bitxor,
##                 FloorDiv,
                LeftShift,
##                 Mod,
                Mul,
##                 Pow,
                RightShift,
                Sub,
                Sum, Sum1, Sum2, Sum3,
                EQ,
                NE,
                LT,
                GT,
                LE,
                GE,
                And,
                Or,
                left, right, bit):
    return setupCosimulation(**locals())

class TestBinaryOps(TestCase):

    def binaryBench(self, Ll, Ml, Lr, Mr):

        bit = Signal(bool(0))
        left = Signal(intbv(Ll, min=Ll, max=Ml))
        right = Signal(intbv(Lr, min=Lr, max=Mr))
        M = 2**14
##        Bitand = Signal(intbv(0, min=-2**17, max=2**17))
##        Bitand_v = Signal(intbv(0, min=-2**17, max=2**17))
##         Bitor = Signal(intbv(0)[max(m, n):])
##         Bitor_v = Signal(intbv(0)[max(m, n):])
##         Bitxor = Signal(intbv(0)[max(m, n):])
##         Bitxor_v = Signal(intbv(0)[max(m, n):])
##         FloorDiv = Signal(intbv(0)[m:])
##         FloorDiv_v = Signal(intbv(0)[m:])
        LeftShift = Signal(intbv(0, min=-2**64, max=2**64))
        LeftShift_v = Signal(intbv(0, min=-2**64, max=2**64))
##         Mod = Signal(intbv(0)[m:])
##         Mod_v = Signal(intbv(0)[m:])
        Mul = Signal(intbv(0, min=-2**17, max=2**17))
        Mul_v = Signal(intbv(0, min=-2**17, max=2**17))
##         Pow = Signal(intbv(0)[64:])
##         Pow_v = Signal(intbv(0)[64:])
        RightShift = Signal(intbv(0, min=-M, max=M))
        RightShift_v = Signal(intbv(0, min=-M, max=M))
        Sub, Sub1, Sub2, Sub3 = [Signal(intbv(min=-M, max=M)) for i in range(4)]
        Sub_v, Sub1_v, Sub2_v, Sub3_v = [Signal(intbv(min=-M, max=M)) for i in range(4)]
        Sum, Sum1, Sum2, Sum3 = [Signal(intbv(min=-M, max=M)) for i in range(4)]
        Sum_v, Sum1_v, Sum2_v, Sum3_v = [Signal(intbv(min=-M, max=M)) for i in range(4)]
        EQ, NE, LT, GT, LE, GE = [Signal(bool()) for i in range(6)]
        EQ_v, NE_v, LT_v, GT_v, LE_v, GE_v = [Signal(bool()) for i in range(6)]
        And, Or = [Signal(bool()) for i in range(2)]
        And_v, Or_v, = [Signal(bool()) for i in range(2)]

        binops = toVerilog(binaryOps,
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
                           LeftShift,
##                            Mod,
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
                           And,
                           Or,
                           left, right, bit)
        binops_v = binaryOps_v(binaryOps.__name__,
##                                Bitand_v,
##                                Bitor_v,
##                                Bitxor_v,
##                                FloorDiv_v,
                               LeftShift_v,
##                                Mod_v,
                               Mul_v,
##                                Pow_v,
                               RightShift_v,
                               Sub_v,
                               Sum_v, Sum1_v, Sum2_v, Sum3_v,
                               EQ_v,
                               NE_v,
                               LT_v,
                               GT_v,
                               LE_v,
                               GE_v,
                               And_v,
                               Or_v,
                               left, right, bit)

        def stimulus():
            for i in range(100):
                # bit.next = False
                left.next = randrange(Ll, Ml)
                right.next = randrange(Lr, Mr)
                yield delay(10)
            for j, k in ((Ll, Lr), (Ml-1, Mr-1), (Ll, Mr-1), (Ml-1, Lr)):
                left.next = j
                right.next = k
                yield delay(10)

        def check():
            while 1:
                yield left, right
                bit.next = not bit
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
##                 self.assertEqual(FloorDiv, FloorDiv_v)
                self.assertEqual(LeftShift, LeftShift_v)
##                 self.assertEqual(Mod, Mod_v)
                self.assertEqual(Mul, Mul_v)
                # self.assertEqual(Pow, Pow_v)
                self.assertEqual(RightShift, RightShift_v)
                self.assertEqual(Sub, Sub_v)
                self.assertEqual(Sum, Sum_v)
                self.assertEqual(Sum1, Sum1_v)
                self.assertEqual(Sum2, Sum2_v)
                self.assertEqual(Sum3, Sum3_v)
                self.assertEqual(EQ, EQ_v)
                self.assertEqual(NE, NE_v)
                self.assertEqual(LT, LT_v)
                self.assertEqual(GT, GT_v)
                self.assertEqual(LE, LE_v)
                self.assertEqual(GE, GE_v)
                self.assertEqual(And, And_v)
                self.assertEqual(Or, Or_v)

        return binops, binops_v, stimulus(), check()
    

    def testBinaryOps(self):
        for Ll, Ml, Lr, Mr in (
                                (-254, 236, 0, 4),
                                (-128, 128, -128, 128),
                                (-53, 25, -23, 123),
                                (-23, 145, -66, 12),
                                (23, 34, -34, -16),
                                (-54, -20, 45, 73),
                                (-25, -12, -123, -66),
                              ):
            sim = self.binaryBench(Ll, Ml, Lr, Mr)
            Simulation(sim).run()


            
def unaryOps(
             Not,
             Invert,
             UnaryAdd,
             UnarySub,
             arg):

    @instance
    def logic():
        while 1:
            yield arg
            Not.next = not arg
            Invert.next = ~arg
            UnaryAdd.next = +arg
            UnarySub.next = --arg

    return logic


def unaryOps_v(name,
               Not,
               Invert,
               UnaryAdd,
               UnarySub,
               arg):
   return setupCosimulation(**locals())


            
class TestUnaryOps(TestCase):

    def unaryBench(self, m):

        M = 2**m

        arg = Signal(intbv(0, min=-M, max=+M))
        Not = Signal(bool(0))
        Not_v = Signal(bool(0))
        Invert = Signal(intbv(0, min=-M, max=+M))
        Invert_v = Signal(intbv(0, min=-M, max=+M))
        UnaryAdd = Signal(intbv(0, min=-M, max=+M))
        UnaryAdd_v = Signal(intbv(0, min=-M, max=+M))
        UnarySub = Signal(intbv(0, min=-M, max=+M))
        UnarySub_v = Signal(intbv(0, min=-M, max=+M))

        unaryops = toVerilog(unaryOps,
                             Not,
                             Invert,
                             UnaryAdd,
                             UnarySub,
                             arg)
        unaryops_v = unaryOps_v(unaryOps.__name__,
                                Not_v,
                                Invert_v,
                                UnaryAdd_v,
                                UnarySub_v,
                                arg)

        def stimulus():
            for i in range(-M, M):
                arg.next = intbv(i)
                yield delay(10)
            for i in range(100):
                arg.next = randrange(-M, M)
                yield delay(10)
            raise StopSimulation

        def check():
            while 1:
                yield arg
                yield delay(1)
                self.assertEqual(Not, Not_v)
                self.assertEqual(Invert, Invert_v)
                self.assertEqual(UnaryAdd, UnaryAdd_v)
                self.assertEqual(UnarySub, UnarySub_v)

        return unaryops, unaryops_v, stimulus(), check()

    def testUnaryOps(self):
        for m in (4, 7):
            sim = self.unaryBench(m)
            Simulation(sim).run()


def augmOps(
##               Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
              LeftShift,
##               Mod,
              Mul,
              RightShift,
              Sub,
              Sum,
              left, right):

    @instance
    def logic():
        var = intbv(0, min=-2**17, max=+2**17)
        var2 = intbv(0, min=-2**64, max=+2**64)
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
            if left < 256 and right < 40 and right >= 0:
                var2[:] = left
                var2 <<= right
                LeftShift.next = var2
    ##         if right != 0:
    ##             var[:] = left
    ##             var %= right
    ##             Mod.next = var
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


def augmOps_v(  name,
##                 Bitand,
##                 Bitor,
##                 Bitxor,
##                 FloorDiv,
                LeftShift,
##                 Mod,
                Mul,
                RightShift,
                Sub,
                Sum,
                left, right):
    return setupCosimulation(**locals())

class TestAugmOps(TestCase):

    def augmBench(self, Ll, Ml, Lr, Mr):

        
        left = Signal(intbv(Ll, min=Ll, max=Ml))
        right = Signal(intbv(Lr, min=Lr, max=Mr))
        M = 2**17

        
##         Bitand = Signal(intbv(0)[max(m, n):])
##         Bitand_v = Signal(intbv(0)[max(m, n):])
##         Bitor = Signal(intbv(0)[max(m, n):])
##         Bitor_v = Signal(intbv(0)[max(m, n):])
##         Bitxor = Signal(intbv(0)[max(m, n):])
##         Bitxor_v = Signal(intbv(0)[max(m, n):])
        
##         FloorDiv = Signal(intbv(0)[m:])
##         FloorDiv_v = Signal(intbv(0)[m:])
        LeftShift = Signal(intbv(0, min=-2**64, max=2**64))
        LeftShift_v = Signal(intbv(0, min=-2**64, max=2**64))
##         Mod = Signal(intbv(0)[m:])
##         Mod_v = Signal(intbv(0)[m:])
        
        Mul = Signal(intbv(0, min=-M, max=+M))
        Mul_v = Signal(intbv(0, min=-M, max=+M))
        
        RightShift = Signal(intbv(0, min=-M, max=+M))
        RightShift_v = Signal(intbv(0, min=-M, max=+M))

        Sub = Signal(intbv(0, min=-M, max=+M))
        Sub_v = Signal(intbv(0, min=-M, max=+M))
        Sum = Signal(intbv(0, min=-M, max=+M))
        Sum_v = Signal(intbv(0, min=-M, max=+M))

        augmops = toVerilog(augmOps,
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
                           LeftShift,
##                            Mod,
                           Mul,
                           RightShift,
                           Sub,
                           Sum,
                           left, right)
        augmops_v = augmOps_v( augmOps.__name__,
##                                Bitand_v,
##                                Bitor_v,
##                                Bitxor_v,
##                                FloorDiv_v,
                               LeftShift_v,
##                                Mod_v,
                               Mul_v,
                               RightShift_v,
                               Sub_v,
                               Sum_v,
                               left, right)

        def stimulus():
            for i in range(100):
                left.next = randrange(Ll, Ml)
                right.next = randrange(Lr, Mr)
                yield delay(10)
            for j, k in ((Ll, Lr), (Ml-1, Mr-1), (Ll, Mr-1), (Ml-1, Lr)):
                left.next = j
                right.next = k
                yield delay(10)

        def check():
            while 1:
                yield left, right
                yield delay(1)
                # print "%s %s %s %s" % (left, right, Or, Or_v)
##                 self.assertEqual(Bitand, Bitand_v)
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
##                 self.assertEqual(FloorDiv, FloorDiv_v)
##                 self.assertEqual(LeftShift, LeftShift_v)
##                 self.assertEqual(Mod, Mod_v)
                self.assertEqual(Mul, Mul_v)
                self.assertEqual(RightShift, RightShift_v)
                self.assertEqual(Sub, Sub_v)
                self.assertEqual(Sum, Sum_v)

        return augmops, augmops_v, stimulus(), check()
    

    def testAugmOps(self):
       for Ll, Ml, Lr, Mr in (
                                (-254, 236, 0, 4),
                                (-128, 128, -128, 128),
                                (-53, 25, -23, 123),
                                (-23, 145, -66, 12),
                                (23, 34, -34, -16),
                                (-54, -20, 45, 73),
                                (-25, -12, -123, -66),
                              ):
            sim = self.augmBench(Ll, Ml, Lr, Mr)
            Simulation(sim).run()


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
        # a.next = d & c
        # b.next = c + (d & c)
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
        
def expressions_v(a, b, clk):
   return setupCosimulation(**locals())
        

class TestExpressions(TestCase):

    def bench(self):
        
        a, a_v = [Signal(intbv(0, min=-34, max=47)) for i in range(2)]
        b, b_v = [Signal(intbv(0, min=0, max=47)) for i in range(2)]
        clk = Signal(bool())
        
        expr = toVerilog(expressions, a, b, clk)
        expr_v = toVerilog(expressions, a_v, b_v, clk)

        @instance
        def check():
            while 1:
                yield clk.posedge
                yield delay(1)
                self.assertEqual(a, a_v)
                # print a
                # print a_v
                self.assertEqual(b, b_v)

        @always(delay(10))
        def clkgen():
            clk.next = not clk

        return expr, expr_v, check, clkgen
    
    def testExpressions(self):
        sim = self.bench()
        Simulation(sim).run()



if __name__ == '__main__':
    unittest.main()


