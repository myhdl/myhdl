from __future__ import absolute_import
import myhdl
from myhdl import *

from glibc_random import glibc_random

def max2(z, a, b):

    @always_comb
    def logic():
        if a > b:
            z.next = a
        else:
            z.next = b

    return logic

def maxn(z, a):
    L = len(a)
    assert L
    assert L % 2 == 0
    H = L // 2
    W = len(a[0])
    if L == 2:
        comp2 = max2(z, a[1], a[0])
        return comp2
    else:
        zlo = Signal(intbv(0)[W:])
        zhi = Signal(intbv(0)[W:])
        complo = maxn(zlo, a[H:])
        comphi = maxn(zhi, a[:H])
        comp2 = max2(z, zhi, zlo)
        return comp2, complo, comphi


def test_findmax():

    L = 32
    W = 16
    
    random_word = Signal(intbv(0)[L*W:])
    clock = Signal(bool())
    stopped = Signal(bool())
    a = [Signal(intbv(0)[W:]) for i in range(L)]
    z = Signal(intbv(0)[W:])

    dut = maxn(z, a)

    @instance
    def clockgen():
        clock.next = 0
        yield delay(10)
        while not stopped:
            clock.next = not clock
            yield delay(10)
        
    @instance
    def stimulus():
        stopped.next = 0
        yield delay(10)
        exp = intbv(0)[W:]
        val = intbv(0)[W:]
        random_word = intbv(0)[32:]
        random_word[:] = 93
        for i in range(2**18):
            exp[:] = 0
            for s in range(L):
                random_word[:] = glibc_random(random_word)
                val[:] = random_word[W:]
                if exp < val:
                    exp[:] = val 
                a[s].next = val 
            yield clock.negedge
            assert z == exp
        stopped.next = 1 
        yield delay(10)
            
    return dut, clockgen, stimulus
    
if __name__ == '__main__':    
    sim = Simulation(test_findmax())
    sim.run()

