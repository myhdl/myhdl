import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *

def binaryOps(
              Bitand,
              Bitor,
              Bitxor,
              FloorDiv,
              Mod,
              Mul,
              Sub,
              Sum,
              EQ,
              NE,
              LT,
              GT,
              LE,
              GE,
              And,
              Or,
              left, right):
   while 1:
        yield left, right
        Bitand.next = left & right
        Bitor.next = left | right
        Bitxor.next = left ^ right
        if right != 0:
            FloorDiv.next = left // right
        if right != 0:
            Mod.next = left % right
        Mul.next = left * right
        if left >= right:
            Sub.next = left - right
        Sum.next = left + right
        EQ.next = left == right
        NE.next = left != right
        LT.next = left < right
        GT.next = left > right
        LE.next = left <= right
        GE.next = left >= right
        And.next = bool(left and right)
        Or.next = bool(left or right)
        
            
 
def binaryOps_v(
                Bitand,
                Bitor,
                Bitxor,
                FloorDiv,
                Mod,
                Mul,
                Sub,
                Sum,
                EQ,
                NE,
                LT,
                GT,
                LE,
                GE,
                And,
                Or,
                left, right):
    analyze_cmd = "iverilog -o binops binops.v tb_binops.v"
    simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi binops"
    if path.exists("ops"):
        os.remove("ops")
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestOps(TestCase):

    def binaryBench(self, m, n):

        M = 2**m
        N = 2**n

        left = Signal(intbv(0)[m:])
        right = Signal(intbv(0)[n:])
        print max(m, n)
        Bitand = Signal(intbv(0)[max(m, n):])
        Bitand_v = Signal(intbv(0)[max(m, n):])
        Bitor = Signal(intbv(0)[max(m, n):])
        Bitor_v = Signal(intbv(0)[max(m, n):])
        Bitxor = Signal(intbv(0)[max(m, n):])
        Bitxor_v = Signal(intbv(0)[max(m, n):])
        FloorDiv = Signal(intbv(0)[m:])
        FloorDiv_v = Signal(intbv(0)[m:])
        Mod = Signal(intbv(0)[m:])
        Mod_v = Signal(intbv(0)[m:])
        Mul = Signal(intbv(0)[m+n:])
        Mul_v = Signal(intbv(0)[m+n:])
        Sub = Signal(intbv(0)[max(m, n):])
        Sub_v = Signal(intbv(0)[max(m, n):])
        Sum = Signal(intbv(0)[max(m, n)+1:])
        Sum_v = Signal(intbv(0)[max(m, n)+1:])
        EQ, NE, LT, GT, LE, GE = [Signal(bool()) for i in range(6)]
        EQ_v, NE_v, LT_v, GT_v, LE_v, GE_v = [Signal(bool()) for i in range(6)]
        And, Or = [Signal(bool()) for i in range(2)]
        And_v, Or_v, = [Signal(bool()) for i in range(2)]
                      
        binops = toVerilog(binaryOps,
                           Bitand,
                           Bitor,
                           Bitxor,
                           FloorDiv,
                           Mod,
                           Mul,
                           Sub,
                           Sum,
                           EQ,
                           NE,
                           LT,
                           GT,
                           LE,
                           GE,
                           And,
                           Or,
                           left, right)
        binops_v = binaryOps_v(
                               Bitand_v,
                               Bitor_v,
                               Bitxor_v,
                               FloorDiv_v,
                               Mod_v,
                               Mul_v,
                               Sub_v,
                               Sum_v,
                               EQ_v,
                               NE_v,
                               LT_v,
                               GT_v,
                               LE_v,
                               GE_v,
                               And_v,
                               Or_v,
                               left, right)

        def stimulus():
            for i in range(min(M, N)):
                # print i
                left.next = intbv(i)
                right.next = intbv(i)
                yield delay(10)
            for i in range(100):
                left.next = randrange(M)
                right.next = randrange(N)
                yield delay(10)
            for j, k in ((0, 0), (0, N-1), (M-1, 0), (M-1, N-1)):
                left.next = j
                right.next = k
                yield delay(10)

        def check():
            while 1:
                yield left, right
                yield delay(1)
                # print "%s %s %s %s" % (left, right, Or, Or_v)
                self.assertEqual(Bitand, Bitand_v)
                self.assertEqual(Bitor, Bitor_v)
                self.assertEqual(Bitxor, Bitxor_v)
                self.assertEqual(FloorDiv, FloorDiv_v)
                self.assertEqual(Mod, Mod_v)
                self.assertEqual(Mul, Mul_v)
                self.assertEqual(Sub, Sub_v)
                self.assertEqual(Sum, Sum_v)
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
        for m, n in ((4, 4,), (5, 3), (2, 6)):
            sim = self.binaryBench(m, n)
            Simulation(sim).run()
    

if __name__ == '__main__':
    unittest.main()
    

