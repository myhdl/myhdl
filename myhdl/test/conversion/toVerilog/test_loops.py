from __future__ import absolute_import
import os
path = os.path
import unittest
from random import randrange


from myhdl import *

from util import setupCosimulation

def ForLoop1(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in downrange(len(a)):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

def ForLoop2(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in downrange(len(a), 5):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

def ForLoop3(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in downrange(len(a), 3, 2):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic
        
def ForLoop4(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in range(len(a)):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

def ForLoop5(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in range(6, len(a)):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

def ForLoop6(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in range(5, len(a), 3):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

def ForContinueLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in downrange(len(a)):
                if a[i] == 0:
                    continue
                var += 1
            out.next = var
    return logic

def ForBreakLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            out.next = 0
            for i in downrange(len(a)):
                if a[i] == 1:
                    out.next = i
                    break
    return logic

def ForBreakContinueLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            out.next = 0
            for i in downrange(len(a)):
                if a[i] == 0:
                    continue
                out.next = i
                break
    return logic

def NestedForLoop1(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in downrange(len(a)):
                if a[i] == 0:
                    continue
                else:
                    for j in downrange(i):
                        if a[j] == 0:
                            var +=1
                    break
            out.next = var
    return logic

def NestedForLoop2(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            out.next = 0
            for i in downrange(len(a)):
                if a[i] == 0:
                    continue
                else:
                    for j in downrange(i-1):
                        if a[j] == 0:
                            pass
                        else:
                            out.next = j
                            break
                    break
    return logic

def ReturnFromFunction(a):
       for i in downrange(len(a)):
            if a[i] == 1:
                return i
       return 0

def FunctionCall(a, out):
    @instance
    def logic():
        while 1:
            yield a
            out.next = ReturnFromFunction(a)
    return logic

# During the following check, I noticed that non-blocking assignments
# are not scheduled when a task is disabled in Icarus. Apparently
# this is one of the many vague areas in the Verilog standard.
def ReturnFromTask(a, out):
    for i in downrange(len(a)):
        if a[i] == 1:
            out[:] = i
            return
    out[:] = 23 # to notice it

def TaskCall(a, out):
    @instance
    def logic():
        var = intbv(0)[8:]
        while 1:
            yield a
            ReturnFromTask(a, var)
            out.next = var
    return logic

def WhileLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            i = len(a)-1
            while i >= 0:
                if a[i] == 1:
                    var += 1
                i -= 1
            out.next = var
    return logic


def WhileContinueLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            i = len(a)-1
            while i >= 0:
                if a[i] == 0:
                    i -= 1
                    continue
                var += 1
                i -= 1
            out.next = var
    return logic
        
def WhileBreakLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            i = len(a)-1
            out.next = 0
            while i >= 0:
                if a[i] == 1:
                    out.next = i
                    break
                i -= 1
    return logic
    
def WhileBreakContinueLoop(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            i = len(a)-1
            out.next = 0
            while i >= 0:
                if a[i] == 0:
                     i -= 1
                     continue
                out.next = i
                break
    return logic
    
        
def LoopTest_v(name, a, out):
    return setupCosimulation(**locals())

class TestLoops(unittest.TestCase):

    def bench(self, LoopTest):
        
        a = Signal(intbv(-1)[16:])
        out_v = Signal(intbv(0)[16:])
        out = Signal(intbv(0)[16:])

        looptest_inst = toVerilog(LoopTest, a, out)
        # looptest_inst = LoopTest(hec, header)
        looptest_v_inst = LoopTest_v(LoopTest.__name__, a, out_v)
 
        def stimulus():
            for i in range(100):
                a.next = randrange(2**min(i, 16))
                yield delay(10)
                # print "%s %s" % (out, out_v)
                self.assertEqual(out, out_v)

        return stimulus(), looptest_inst, looptest_v_inst

    def testForLoop1(self):
        sim = self.bench(ForLoop1)
        Simulation(sim).run()
        
    def testForLoop2(self):
        sim = self.bench(ForLoop2)
        Simulation(sim).run()
        
    def testForLoop3(self):
        sim = self.bench(ForLoop3)
        Simulation(sim).run()
        
    def testForLoop4(self):
        sim = self.bench(ForLoop4)
        Simulation(sim).run()
        
    def testForLoop5(self):
        sim = self.bench(ForLoop5)
        Simulation(sim).run()
        
    def testForLoop6(self):
        sim = self.bench(ForLoop6)
        Simulation(sim).run()
        
    def testForContinueLoop(self):
        sim = self.bench(ForContinueLoop)
        Simulation(sim).run()
        
    def testForBreakLoop(self):
        sim = self.bench(ForBreakLoop)
        Simulation(sim).run()
        
    def testForBreakContinueLoop(self):
        sim = self.bench(ForBreakContinueLoop)
        Simulation(sim).run()
        
    def testNestedForLoop1(self):
        sim = self.bench(NestedForLoop1)
        Simulation(sim).run()
        
    def testNestedForLoop2(self):
        sim = self.bench(NestedForLoop2)
        Simulation(sim).run()
        
    def testNestedForLoop2(self):
        sim = self.bench(NestedForLoop2)
        Simulation(sim).run()

    def testFunctionCall(self):
        sim = self.bench(FunctionCall)
        Simulation(sim).run()
        
    def testTaskCall(self):
        sim = self.bench(TaskCall)
        Simulation(sim).run()
       
    def testWhileLoop(self):
        sim = self.bench(WhileLoop)
        Simulation(sim).run()

    def testWhileContinueLoop(self):
        sim = self.bench(WhileContinueLoop)
        Simulation(sim).run()

    def testWhileBreakLoop(self):
        sim = self.bench(WhileBreakLoop)
        Simulation(sim).run()
        
    def testWhileBreakContinueLoop(self):
        sim = self.bench(WhileBreakContinueLoop)
        Simulation(sim).run()

        
if __name__ == '__main__':
    unittest.main()
