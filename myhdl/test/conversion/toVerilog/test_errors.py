from __future__ import absolute_import
import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

ACTIVE_LOW, INACTIVE_HIGH = 0, 1


def freeVarTypeError(count, enable, clock, reset, n):
    cnt = intbv(0)[8:]
    def incTaskFunc():
        if enable:
            cnt[:] = (cnt + 1) % n
    @instance
    def incTaskGen():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
               cnt[:]= 0
            else:
                incTaskFunc()
    return incTaskGen

def multipleDrivenSignal(count, enable, clock, reset, n):
    @instance
    def incTaskGen():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return incTaskGen, incTaskGen

def shadowingSignal(count, enable, clock, reset, n):
    count = Signal(intbv(0)[8:])
    @instance
    def incTaskGen():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return incTaskGen

def internalSignal(count, enable, clock, reset, n):
    @instance
    def logic():
        a = Signal(bool())
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return logic

def undefinedBitWidthSignal(count, enable, clock, reset, n):
    count = Signal(intbv(0))
    @instance
    def incTaskGen():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
               count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return incTaskGen
                


def yieldObject1(count, enable, clock, reset, n):
    @instance
    def logic():
        while 1:
            yield clock.posedge, delay(5)
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return logic
                
def g1(clock):
        yield clock.posedge
def g2(reset):
        yield reset.negedge
      
def yieldObject2(count, enable, clock, reset, n):
    @instance
    def logic():
        while 1:
            yield g1(clock), g2(reset)
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return logic

def f1(n):
    if n == 0:
        return 0
    else:
        return f1(n-1)

def f2(n):
    if n == 0:
        return 1
    else:
        return f3(n-1)
    
def f3(n):
    if n == 0:
        return 1
    else:
        return f2(n-1)
      
def recursion1(count, enable, clock, reset, n):
    @instance
    def logic():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = f1(n)
    return logic
                
def recursion2(count, enable, clock, reset, n):
    @instance
    def logic():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = f2(n)
    return logic

def h1(n):
    return None

def functionNoReturnVal(count, enable, clock, reset, n):
    @instance
    def logic():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = h1(n)
    return logic
                
def h2(cnt):
    cnt[:] = cnt + 1
    return 1

def taskReturnVal(count, enable, clock, reset, n):
    @instance
    def logic():
        cnt = intbv(0)[8:]
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    h2(cnt)
                    count.next = count + 1
    return logic


def printnlToFile(count, enable, clock, reset, n):
    @instance
    def logic():
        cnt = intbv(0)[8:]
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    print >> f, count
                    count.next = count + 1
    return logic

def printToFile(count, enable, clock, reset, n):
    @instance
    def logic():
        cnt = intbv(0)[8:]
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    print >> f, count,
                    count.next = count + 1
    return logic

def listComp1(count, enable, clock, reset, n):
    @instance
    def logic():
        mem = [intbv(0)[8:] for i in range(4) for j in range(5)]
        while 1:
            yield clock.posedge, reset.negedge
            count.next = count + 1
    return logic

def listComp2(count, enable, clock, reset, n):
    @instance
    def logic():
        mem = [intbv(0)[8:] for i in downrange(4)]
        while 1:
            yield clock.posedge, reset.negedge
            count.next = count + 1
    return logic

def listComp3(count, enable, clock, reset, n):
    @instance
    def logic():
        mem = [intbv(0)[8:] for i in range(1, 4)]
        while 1:
            yield clock.posedge, reset.negedge
            count.next = count + 1
    return logic
        
def listComp4(count, enable, clock, reset, n):
    @instance
    def logic():
        mem = [intbv(0) for i in range(4)]
        while 1:
            yield clock.posedge, reset.negedge
            count.next = count + 1
    return logic

def listComp5(count, enable, clock, reset, n):
    @instance
    def logic():
        mem = [i for i in range(4)]
        while 1:
            yield clock.posedge, reset.negedge
            count.next = count + 1
    return logic

def undefinedBitWidthMem(count, enable, clock, reset, n):
    mem = [Signal(intbv(0)[8:]) for i in range(8)]
    mem[7] = Signal(intbv(0))
    @instance
    def f():
        while 1:
            yield clock.posedge, reset.negedge
            count.next = mem[0] + 1
    return f

def inconsistentTypeMem(count, enable, clock, reset, n):
    mem = [Signal(intbv(0)[8:]) for i in range(8)]
    mem[3] = Signal(bool())
    @instance
    def f():
        while 1:
            yield clock.posedge, reset.negedge
            count.next = mem[0] + 1
    return f

def inconsistentBitWidthMem(count, enable, clock, reset, n):
    mem = [Signal(intbv(0)[8:]) for i in range(8)]
    mem[4] = Signal(intbv(0)[7:])
    @instance
    def f():
        while 1:
            yield clock.posedge, reset.negedge
            count.next = mem[0] + 1
    return f


## def listElementNotUnique(count, enable, clock, reset, n):
##     mem = [Signal(intbv(0)[8:]) for i in range(8)]
##     mem2 = mem[4:]
##     def f():
##         while 1:
##             yield clock.posedge, reset.negedge
##             count.next = mem[0] + mem2[1]
##     return f()


class TestErr(TestCase):

    def clockGen(self, clock):
        while 1:
            yield delay(10)
            clock.next = not clock
    
    def stimulus(self, enable, clock, reset):
        reset.next = INACTIVE_HIGH
        yield clock.negedge
        reset.next = ACTIVE_LOW
        yield clock.negedge
        reset.next = INACTIVE_HIGH
        for i in range(1000):
            enable.next = 1
            yield clock.negedge
        for i in range(1000):
            enable.next = min(1, randrange(5))
            yield clock.negedge
        raise StopSimulation

    def check(self, count, count_v, enable, clock, reset, n):
        expect = 0
        yield reset.posedge
        self.assertEqual(count, expect)
        self.assertEqual(count, count_v)
        while 1:
            yield clock.posedge
            if enable:
                expect = (expect + 1) % n
            yield delay(1)
            # print "%d count %s expect %s count_v %s" % (now(), count, expect, count_v)
            self.assertEqual(count, expect)
            self.assertEqual(count, count_v)
                
    def bench(self, err):

        m = 8
        n = 2 ** m
 
        count = Signal(intbv(0)[m:])
        count_v = Signal(intbv(0)[m:])
        enable = Signal(bool(0))
        clock, reset = [Signal(bool()) for i in range(2)]

        err_inst = toVerilog(err, count, enable, clock, reset, n=n)
        clk_1 = self.clockGen(clock)
        st_1 = self.stimulus(enable, clock, reset)
        ch_1 = self.check(count, count_v, enable, clock, reset, n=n)

        sim = Simulation(err_inst, clk_1, st_1, ch_1)
        return sim


    def testInternalSignal(self):
        try:
            self.bench(internalSignal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.TypeInfer)
        else:
            self.fail()
            
    def testMultipleDrivenSignal(self):
        try:
            self.bench(multipleDrivenSignal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.SigMultipleDriven)
        else:
            self.fail()
            
    def testShadowingSignal(self):
        try:
            self.bench(shadowingSignal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.ShadowingSignal)
        else:
            self.fail()

    def testUndefinedBitWidthSignal(self):
        try:
            self.bench(undefinedBitWidthSignal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UndefinedBitWidth)
        else:
            self.fail()
        
    def testFreeVarTypeError(self):
        try:
            self.bench(freeVarTypeError)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.FreeVarTypeError)
        else:
            self.fail()
        
##     def testNegIntbv(self):
##         try:
##             self.bench(negIntbv)
##         except ConversionError, e:
##             self.assertEqual(e.kind, _error.IntbvSign)
##         else:
##             self.fail()
            
    def testYield1(self):
        try:
            self.bench(yieldObject1)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UnsupportedYield)
        else:
            self.fail()
            
    def testYield2(self):
        try:
            self.bench(yieldObject2)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testRecursion1(self):
        try:
            self.bench(recursion1)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testRecursion2(self):
        try:
            self.bench(recursion2)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testFunctionNoReturnVal(self):
        try:
            self.bench(functionNoReturnVal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testTaskReturnVal(self):
        try:
            self.bench(taskReturnVal)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()

    def testPrintnlToFile(self):
        try:
            self.bench(printnlToFile)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()

    def testPrintToFile(self):
        try:
            self.bench(printToFile)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
            
    def testListComp1(self):
        try:
            self.bench(listComp1)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        else:
            self.fail()
           
    def testListComp2(self):
        try:
            self.bench(listComp2)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UnsupportedListComp)
        else:
            self.fail()
           
    def testListComp3(self):
        try:
            self.bench(listComp3)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UnsupportedListComp)
        else:
            self.fail()
           
    def testListComp4(self):
        try:
            self.bench(listComp4)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UnsupportedListComp)
        else:
            self.fail()
           
    def testListComp5(self):
        try:
            self.bench(listComp5)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UnsupportedListComp)
        else:
            self.fail()
        
    def testUndefinedBitWidthMem(self):
        try:
            self.bench(undefinedBitWidthMem)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.UndefinedBitWidth)
        else:
            self.fail()
            
    def testInconsistentTypeMem(self):
        try:
            self.bench(inconsistentTypeMem)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.InconsistentType)
        else:
            self.fail()
        
    def testInconsistentBitWidthMem(self):
        try:
            self.bench(inconsistentBitWidthMem)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.InconsistentBitWidth)
        else:
            self.fail()
            
##     def testListElementNotUnique(self):
##         try:
##             self.bench(listElementNotUnique)
##         except ConversionError, e:
##             self.assertEqual(e.kind, _error.ListElementNotUnique)
##         else:
##             self.fail()


if __name__ == '__main__':
    unittest.main()


            
            

    

    
        


                

        

