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
##               Bitand,
##               Bitor,
##               Bitxor,
##               FloorDiv,
##               LeftShift,
##               Mod,
              Mul,
##               Pow,
##               RightShift,
##               Sub,
              Sum,
##               EQ,
##               NE,
##               LT,
##               GT,
##               LE,
##               GE,
##               And,
##               Or,
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
##             Mod.next = left % right
        Mul.next = left * right
##         # Icarus doesn't support ** yet
##         #if left < 256 and right < 40:
##         #    Pow.next = left ** right
##         Pow.next = 0
##         RightShift.next = left >> right
##         if left >= right:
##             Sub.next = left - right
        Sum.next = left + right
##         EQ.next = left == right
##         NE.next = left != right
##         LT.next = left < right
##         GT.next = left > right
##         LE.next = left <= right
##         GE.next = left >= right
##         And.next = bool(left and right)
##         Or.next = bool(left or right)



def binaryOps_v(name,
##                 Bitand,
##                 Bitor,
##                 Bitxor,
##                 FloorDiv,
##                 LeftShift,
##                 Mod,
                Mul,
##                 Pow,
##                 RightShift,
##                 Sub,
                Sum,
##                 EQ,
##                 NE,
##                 LT,
##                 GT,
##                 LE,
##                 GE,
##                 And,
##                 Or,
                left, right):
    return setupCosimulation(**locals())

class TestBinaryOps(TestCase):

    def binaryBench(self, Ll, Ml, Lr, Mr):

        left = Signal(intbv(min=Ll, max=Ml))
        right = Signal(intbv(min=Lr, max=Mr))
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
##         Mod = Signal(intbv(0)[m:])
##         Mod_v = Signal(intbv(0)[m:])
        Mul = Signal(intbv(0, min=-2**17, max=2**17))
        Mul_v = Signal(intbv(0, min=-2**17, max=2**17))
##         Pow = Signal(intbv(0)[64:])
##         Pow_v = Signal(intbv(0)[64:])
##         RightShift = Signal(intbv(0)[m:])
##         RightShift_v = Signal(intbv(0)[m:])
##         Sub = Signal(intbv(0)[max(m, n):])
##         Sub_v = Signal(intbv(0)[max(m, n):])
        Sum = Signal(intbv(min=Ll+Lr, max=Ml+Mr-1))
        Sum_v = Signal(intbv(min=Ll+Lr, max=Ml+Mr-1))
        Sum = Signal(intbv(min=-2**14, max=2**14))
        Sum_v = Signal(intbv(min=-2**14, max=2**14))
##         EQ, NE, LT, GT, LE, GE = [Signal(bool()) for i in range(6)]
##         EQ_v, NE_v, LT_v, GT_v, LE_v, GE_v = [Signal(bool()) for i in range(6)]
##         And, Or = [Signal(bool()) for i in range(2)]
##         And_v, Or_v, = [Signal(bool()) for i in range(2)]

        binops = toVerilog(binaryOps,
##                            Bitand,
##                            Bitor,
##                            Bitxor,
##                            FloorDiv,
##                            LeftShift,
##                            Mod,
                           Mul,
##                            Pow,
##                            RightShift,
##                            Sub,
                           Sum,
##                            EQ,
##                            NE,
##                            LT,
##                            GT,
##                            LE,
##                            GE,
##                            And,
##                            Or,
                           left, right)
        binops_v = binaryOps_v(binaryOps.func_name,
##                                Bitand_v,
##                                Bitor_v,
##                                Bitxor_v,
##                                FloorDiv_v,
##                                LeftShift_v,
##                                Mod_v,
                               Mul_v,
##                                Pow_v,
##                                RightShift_v,
##                                Sub_v,
                               Sum_v,
##                                EQ_v,
##                                NE_v,
##                                LT_v,
##                                GT_v,
##                                LE_v,
##                                GE_v,
##                                And_v,
##                                Or_v,
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
            
                #print "%s %s %s %s" % (left, right, Mul, Mul_v)
                #print "%s %s %s %s" % (left, right, bin(Mul), bin(Mul_v))
                #print "%s %s %s %s" % (left, right, Sum, Sum_v)
                #print "%s %s %s %s" % (left, right, bin(Sum), bin(Sum_v))
##                 self.assertEqual(Bitand, Bitand_v)
##                 self.assertEqual(Bitor, Bitor_v)
##                 self.assertEqual(Bitxor, Bitxor_v)
##                 self.assertEqual(FloorDiv, FloorDiv_v)
##                 self.assertEqual(LeftShift, LeftShift_v)
##                 self.assertEqual(Mod, Mod_v)
                self.assertEqual(Mul, Mul_v)
                # self.assertEqual(Pow, Pow_v)
##                 self.assertEqual(RightShift, RightShift_v)
##                 self.assertEqual(Sub, Sub_v)
                self.assertEqual(Sum, Sum_v)
##                 self.assertEqual(EQ, EQ_v)
##                 self.assertEqual(NE, NE_v)
##                 self.assertEqual(LT, LT_v)
##                 self.assertEqual(GT, GT_v)
##                 self.assertEqual(LE, LE_v)
##                 self.assertEqual(GE, GE_v)
##                 self.assertEqual(And, And_v)
##                 self.assertEqual(Or, Or_v)

        return binops, binops_v, stimulus(), check()
    

    def testBinaryOps(self):
        for Ll, Ml, Lr, Mr in ( (-128, 128, -128, 128),
                                (-53, 25, -23, 123),
                                (-23, 145, -66, 12),
                                (23, 34, -34, -16),
                                (-54, -20, 45, 73),
                                (-25, -12, -123, -66),
                              ):
            sim = self.binaryBench(Ll, Ml, Lr, Mr)
            Simulation(sim).run()
                

if __name__ == '__main__':
    unittest.main()


