from __future__ import absolute_import
import os
path = os.path
from random import randrange

import pytest

import myhdl
from myhdl import *
from myhdl.conversion import verify, analyze
from myhdl import ConversionError
from myhdl.conversion._misc import _error

@block
def ForLoopError1(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in (1, 2, 3):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic
        
@block
def ForLoopError2(a, out):
    @instance
    def logic():
        while 1:
            yield a
            var = 0
            for i in list((1, 2, 3)):
                if a[i] == 1:
                    var += 1
            out.next = var
    return logic

@block
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

@block
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

@block
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
        
@block
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

@block
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

@block
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

@block
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

@block
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

@block
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

@block
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

@block
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

@block
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

@block
def TaskCall(a, out):
    @instance
    def logic():
        var = intbv(0)[8:]
        while 1:
            yield a
            ReturnFromTask(a, var)
            out.next = var
    return logic

@block
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

@block
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
        
@block
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
    
@block
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
    
# for loop 3 and 6 can't work in vhdl
loops = [ForLoop1, ForLoop2, ForLoop4, ForLoop5, ForContinueLoop, ForBreakLoop,
      ForBreakContinueLoop, NestedForLoop1, NestedForLoop2, FunctionCall,
      WhileLoop, WhileContinueLoop, WhileBreakLoop, WhileBreakContinueLoop]

@pytest.mark.parametrize('LoopTest', loops)
@pytest.mark.verify_convert
@block
def test_loop(LoopTest):

    a = Signal(intbv(-1)[16:])
    z = Signal(intbv(0)[16:])

    looptest_inst = LoopTest(a, z)
    data = tuple([randrange(2**min(i, 16)) for i in range(100)])

    @instance
    def stimulus():
        for i in range(100):
            a.next = data[i]
            yield delay(10)
            print(z)

    return stimulus, looptest_inst


def testForLoopError1():
    with pytest.raises(ConversionError) as e:
        test_loop(ForLoopError1).analyze_convert()
    assert e.value.kind == _error.Requirement
    
def testForLoopError2():
    with pytest.raises(ConversionError) as e:
        analyze(test_loop(ForLoopError2))
    assert e.value.kind == _error.Requirement

# for loop 3 and 6 can't work in vhdl
lc = [ForLoop1, ForLoop2, ForLoop4, ForLoop5, ForContinueLoop, ForBreakLoop,
      ForBreakContinueLoop, NestedForLoop1, NestedForLoop2, FunctionCall,
      WhileLoop, WhileContinueLoop, WhileBreakLoop, WhileBreakContinueLoop]


## def testTaskCall(self):
##     sim = self.bench(TaskCall)
##     Simulation(sim).run()
