import os
path = os.path
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2)
import time

import myhdl
from myhdl import *
from myhdl.conversion import verify

N = 8
M = 2 ** N
DEPTH = 5

@block
def xor(z, a, b, c):
    @instance
    def logic():
        while 1:
            yield a, b, c
            z.next = a ^ b ^ c
    return logic

def randOthers(i, n):
    l = list(range(n))
    l.remove(i)
    random.shuffle(l)
    return l[0], l[1]

@block
def randscrambler(ol, il, stage=0):
    """ Recursive hierarchy of random xor gates.

    An invented module to check hierarchy with toVerilog.

    """

    sl1 = [Signal(bool()) for i in range(N)]
    sl2 = [Signal(bool()) for i in range(N)]
    i1 = [None] * N
    i2 = [None] * N

    if stage < DEPTH:
        for i in range(N):
            j, k = randOthers(i, N)
            i1[i] = xor(sl1[i], il[i], il[j], il[k])
        rs = randscrambler(sl2, sl1, stage=stage+1)
        for i in range(N):
            j, k = randOthers(i, N)
            i2[i] = xor(ol[i], sl2[i], sl2[j], sl2[k])
        return i1, i2, rs
    else:
        for i in range(N):
            j, k = randOthers(i, N)
            i1[i] = xor(ol[i], il[i], il[j], il[k])
        return i1

@block
def randscrambler_top(o7, o6, o5, o4, o3, o2, o1, o0,
                    i7, i6, i5, i4, i3, i2, i1, i0):
    sl1 = [i7, i6, i5, i4, i3, i2, i1, i0]
    sl2 = [o7, o6, o5, o4, o3, o2, o1, o0]
    rs = randscrambler(sl2, sl1, stage=0)
    return rs

o7, o6, o5, o4, o3, o2, o1, o0 = [Signal(bool()) for i in range(N)]
i7, i6, i5, i4, i3, i2, i1, i0 = [Signal(bool()) for i in range(N)]
v7, v6, v5, v4, v3, v2, v1, v0 = [Signal(bool()) for i in range(N)]

@block
def randscramblerBench():

    @instance
    def stimulus():
        a = modbv(0)[N:]
        z = intbv(0)[N:]
        for i in range(100):

            a[:] += 97
            i7.next = a[7]
            i6.next  = a[6]
            i5.next  = a[5]
            i4.next  = a[4]
            i3.next  = a[3]
            i2.next  = a[2]
            i1.next  = a[1]
            i0.next  = a[0]
            yield delay(10)
            z[7] = o7
            z[6] = o6
            z[5] = o5
            z[4] = o4
            z[3] = o3
            z[2] = o2
            z[1] = o1
            z[0] = o0
            print (a)
            print (z)

    rs = randscrambler_top(
        o7, o6, o5, o4, o3, o2, o1, o0,
        i7, i6, i5, i4, i3, i2, i1, i0
    )

    return rs, stimulus

def test_randscramber():
    assert conversion.verify(randscramblerBench()) == 0
