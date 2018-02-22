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
    
    clock = Signal(bool())
    stopped = Signal(bool())
    
    a0  = Signal(intbv(0)[W:])
    a1  = Signal(intbv(0)[W:])
    a2  = Signal(intbv(0)[W:])
    a3  = Signal(intbv(0)[W:])
    a4  = Signal(intbv(0)[W:])
    a5  = Signal(intbv(0)[W:])
    a6  = Signal(intbv(0)[W:])
    a7  = Signal(intbv(0)[W:])
    a8  = Signal(intbv(0)[W:])
    a9  = Signal(intbv(0)[W:])
    a10 = Signal(intbv(0)[W:])
    a11 = Signal(intbv(0)[W:])
    a12 = Signal(intbv(0)[W:])
    a13 = Signal(intbv(0)[W:])
    a14 = Signal(intbv(0)[W:])
    a15 = Signal(intbv(0)[W:])
    a16 = Signal(intbv(0)[W:])
    a17 = Signal(intbv(0)[W:])
    a18 = Signal(intbv(0)[W:])
    a19 = Signal(intbv(0)[W:])
    a20 = Signal(intbv(0)[W:])
    a21 = Signal(intbv(0)[W:])
    a22 = Signal(intbv(0)[W:])
    a23 = Signal(intbv(0)[W:])
    a24 = Signal(intbv(0)[W:])
    a25 = Signal(intbv(0)[W:])
    a26 = Signal(intbv(0)[W:])
    a27 = Signal(intbv(0)[W:])
    a28 = Signal(intbv(0)[W:])
    a29 = Signal(intbv(0)[W:])
    a30 = Signal(intbv(0)[W:])
    a31 = Signal(intbv(0)[W:])

    a = [
         a0,
         a1 ,
         a2 ,
         a3 ,
         a4 ,
         a5 ,
         a6 ,
         a7 ,
         a8 ,
         a9 ,
         a10,
         a11,
         a12,
         a13,
         a14,
         a15,
         a16,
         a17,
         a18,
         a19,
         a20,
         a21,
         a22,
         a23,
         a24,
         a25,
         a26,
         a27,
         a28,
         a29,
         a30,
         a31
         ]
    
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
        exp = intbv(0)[W:]
        val = intbv(0)[W:]
        v = [intbv(0)[W:] for i in range(L)]
        random_word = intbv(0)[32:]
        random_word[:] = 93
        for i in range(2**18):
            exp[:] = 0
            for s in range(L):
                random_word[:] = glibc_random(random_word)
                val[:] = random_word[W:]
                if exp < val:
                    exp[:] = val
                v[s][:] = val
    
            a0.next  = v[0]         
            a1.next  = v[1]   
            a2.next  = v[2]   
            a3.next  = v[3]   
            a4.next  = v[4]   
            a5.next  = v[5]   
            a6.next  = v[6]   
            a7.next  = v[7]   
            a8.next  = v[8]   
            a9.next  = v[9]   
            a10.next  = v[10]   
            a11.next  = v[11]   
            a12.next  = v[12]   
            a13.next  = v[13]   
            a14.next  = v[14]   
            a15.next  = v[15]   
            a16.next  = v[16]   
            a17.next  = v[17]   
            a18.next  = v[18]   
            a19.next  = v[19]   
            a20.next  = v[20]   
            a21.next  = v[21]   
            a22.next  = v[22]   
            a23.next  = v[23]   
            a24.next  = v[24]   
            a25.next  = v[25]   
            a26.next  = v[26]   
            a27.next  = v[27]   
            a28.next  = v[28]   
            a29.next  = v[29]   
            a30.next  = v[30]   
            a31.next  = v[31]   
 
            yield clock.negedge
            assert z == exp
        stopped.next = 1 
        yield delay(10)
            
    return dut, clockgen, stimulus
    
if __name__ == '__main__':    
    sim = Simulation(test_findmax())
    sim.run()
