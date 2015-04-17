from __future__ import absolute_import
from random import randrange

from myhdl import *


def NumassBench():

    p = Signal(intbv(1)[8:])
    q = Signal(intbv(1)[40:])
    r = Signal(intbv(1, min=-256, max=256))
    s = Signal(intbv(1, min=-2**40, max=2**40))
    PBIGINT = randrange(2**34, 2**40)
    NBIGINT = -randrange(2**34, 2**40)

    @instance
    def check():
        p.next = 0
        q.next = 0
        r.next = 0
        s.next = 0
        yield delay(10)
        print("%d %d %d %d" % (p, q, r, s))
        p.next = 1
        q.next = 1
        r.next = 1
        s.next = 1
        yield delay(10)
        print("%d %d %d %d" % (p, q, r, s))
        p.next = 2
        q.next = 2
        r.next = -2
        s.next = -2
        yield delay(10)
        print("%d %d %d %d" % (p, q, r, s))
        p.next = 255
        q.next = 246836311517
        r.next = 255
        s.next = -246836311517
        yield delay(10)
        print("%d %d %d %d %d %d" % (p, q[40:20], q[20:0], r ,s[41:20], s[20:0]))        
        p.next = 254
        q.next = PBIGINT
        r.next = -256
        s.next = NBIGINT
        yield delay(10)
        print("%d %d %d %d %d %d" % (p, q[40:20], q[20:0], r ,s[41:20], s[20:0]))

    return check


def test_numass():
    assert conversion.verify(NumassBench) == 0
