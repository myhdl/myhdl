import os
path = os.path
import unittest
from random import randrange

from myhdl import *

def ForLoop(a, out):
    while 1:
        yield a
        var = 0
        for i in downrange(len(a)):
            if a[i] == 1:
                var += 1
        out.next = var
        
def ForContinueLoop(a, out):
    while 1:
        yield a
        var = 0
        for i in downrange(len(a)):
            if a[i] == 0:
                continue
            var += 1
        out.next = var

def ForBreakLoop(a, out):
    while 1:
        yield a
        for i in downrange(len(a)):
            if a[i] == 1:
                out.next = i
                break

def ForBreakContinueLoop(a, out):
    while 1:
        yield a
        for i in downrange(len(a)):
            if a[i] == 0:
                continue
            out.next = i
            break
        

def WhileLoop(a, out):
    while 1:
        yield a
        var = 0
        i = len(a)-1
        while i >= 0:
            if a[i] == 1:
                var += 1
            i -= 1
        out.next = var

def WhileContinueLoop(a, out):
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
        
def WhileBreakLoop(a, out):
    while 1:
        yield a
        var = 0
        i = len(a)-1
        while i >= 0:
            if a[i] == 1:
                out.next = i
                break
            i -= 1
    
def WhileBreakContinueLoop(a, out):
    while 1:
        yield a
        var = 0
        i = len(a)-1
        while i >= 0:
            if a[i] == 0:
                 i -= 1
                 continue
            out.next = i
            break
    
        
objfile = "looptest.o"           
analyze_cmd = "iverilog -o %s looptest_inst.v tb_looptest_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
        
def LoopTest_v(a, out):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

class TestLoops(unittest.TestCase):

    def bench(self, LoopTest):
        
        a = Signal(intbv(0)[16:])
        out_v = Signal(intbv(0)[16:])
        out = Signal(intbv(0)[16:])

        looptest_inst = toVerilog(LoopTest, a, out)
        # looptest_inst = LoopTest(hec, header)
        looptest_v_inst = LoopTest_v(a, out_v)
 
        def stimulus():
            for i in range(100):
                a.next = randrange(2**min(i, 16))
                yield delay(10)
                # print "%s %s" % (out, out_v)
                self.assertEqual(out, out_v)

        return stimulus(), looptest_inst, looptest_v_inst

    def testForLoop(self):
        sim = self.bench(ForLoop)
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
