#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Run the unit tests for Signal """
from __future__ import absolute_import


import operator
import random
from random import randrange
random.seed(1) # random, but deterministic
import sys
maxint = sys.maxsize
import types
import copy

import unittest
from unittest import TestCase

from myhdl._simulator import _siglist
from myhdl import intbv, Signal
from myhdl._compat import long

        
class SigTest(TestCase):

    def setUp(self):
        self.vals   = [0, 0, 1, 1, 1, 2, 3, 5, intbv(0), intbv(1), intbv(2)]  
        self.nexts  = [0, 1, 1, 0, 1, 0, 4, 5, intbv(1), intbv(0), intbv(0)]
        self.vals  += [intbv(0), intbv(1), intbv(0), intbv(1), 2           ]
        self.nexts += [intbv(0), intbv(1), 1       , 0       , intbv(3)    ]
        self.vals  += [ [1,2,3], (1,2,3), {1:1, 2:2}, (0, [2, 3], (1, 2))  ]
        self.nexts += [ [4,5,6], (4,5,5), {3:3, 4:4}, (1, (0, 1), [2, 3])  ]
        self.vals  += [bool(0), bool(1), bool(0), bool(1), bool(0), bool(1)]
        self.nexts += [bool(0), bool(1), bool(1), bool(0), 1      , 0      ]
        self.sigs = [Signal(i) for i in self.vals]
        
        self.incompatibleVals  = [ [3, 4], (1, 2),  3 , intbv(0), [1]      ]
        self.incompatibleNexts = [ 4     , 3     , "3", (0)     , intbv(1) ]
        self.incompatibleSigs = [Signal(i) for i in self.incompatibleVals]
        
        self.eventWaiters = [object() for i in range(3)]
        self.posedgeWaiters = [object() for i in range(5)]
        self.negedgeWaiters = [object() for i in range(7)]

        
    def testValAttrReadOnly(self):
        """ val attribute should not be writable"""
        s1 = Signal(1)
        try:
            s1.val = 1
        except AttributeError:
            pass
        else:
            self.fail()

    def testDrivenAttrValue(self):
        """ driven attribute only accepts value 'reg' or 'wire' """
        s1 = Signal(1)
        try:
            s1.driven = "signal"
        except ValueError:
            pass
        else:
            self.fail()
        
    def testPosedgeAttrReadOnly(self):
        """ posedge attribute should not be writable"""
        s1 = Signal(1)
        try:
            s1.posedge = 1
        except AttributeError:
            pass
        else:
            self.fail()
            
    def testNegedgeAttrReadOnly(self):
        """ negedge attribute should not be writable"""
        s1 = Signal(1)
        try:
            s1.negedge = 1
        except AttributeError:
            pass
        else:
            self.fail()

    def testInitDefault(self):
        """ initial value is None by default """
        s1 = Signal()
        self.assertEqual(s1, None)

    def testInitialization(self):
        """ initial val and next should be equal """
        for s in self.sigs:
            self.assertEqual(s.val, s.next)

    def testUpdate(self):
        """ _update() should assign next into val """
        for s, n in zip(self.sigs, self.nexts):
            cur = copy.copy(s.val)
            s.next = n
            # assigning to next should not change current value ...
            self.assertTrue(s.val == cur)
            s._update()
            self.assertTrue(s.val == n)

    def testNextType(self):
        """ sig.next = n should fail on access if type(n) incompatible """
        i = 0
        for s in (self.sigs + self.incompatibleSigs):
            for n in (self.vals + self.incompatibleVals):
                self.assertTrue(isinstance(s.val, s._type))
                if isinstance(s.val, (int, long, intbv)):
                    t = (int, long, intbv)
                else:
                    t = s._type
                if not isinstance(n, t):
                    i += 1
                    try:
                        oldval = s.val
                        s.next = n
                    except (TypeError, ValueError):
                        pass
                    else:
                        self.fail()
        self.assertTrue(i >= len(self.incompatibleSigs), "Nothing tested %s" %i)

    def testAfterUpdate(self):
        """ updated val and next should be equal but not identical """
        for s, n in zip(self.sigs, self.nexts):
            s.next = n
            s._update()
            self.assertEqual(s.val, s.next)
            
    def testModify(self):
        """ Modifying mutable next should be on a copy """
        for s in self.sigs:
            mutable = 0
            try:
                hash(s.val)
            except TypeError:
                mutable = 1
            if not mutable:
                continue
            if type(s.val) is list:
                s.next.append(1)
            elif type(s.val) is dict:
                s.next[3] = 5
            else:
                s.next # plain read access
            self.assertTrue(s.val is not s.next, repr(s.val))

    def testUpdatePosedge(self):
        """ update on posedge should return event and posedge waiters """
        s1 = Signal(1)
        s1.next = 0
        s1._update()
        s1.next = 1
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters + self.posedgeWaiters
        self.assertEqual(set(waiters), set(expected))
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, [])
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
            
    def testUpdateNegedge(self):
        """ update on negedge should return event and negedge waiters """
        s1 = Signal(1)
        s1.next = 1
        s1._update()
        s1.next = 0
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters + self.negedgeWaiters
        self.assertEqual(set(waiters), set(expected))
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, [])

    def testUpdateEvent(self):
        """ update on non-edge event should return event waiters """
        s1 = Signal(1)
        s1.next = 4
        s1._update()
        s1.next = 5
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters
        self.assertEqual(set(waiters), set(expected))
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
        
    def testUpdateNoEvent(self):
        """ update without value change should not return event waiters """
        s1 = Signal(1)
        s1.next = 4
        s1._update()
        s1.next = 4
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        self.assertEqual(waiters, [])
        self.assertEqual(s1._eventWaiters, self.eventWaiters)
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
    
    def testNextAccess(self):
        """ each next attribute access puts a sig in a global siglist """
        del _siglist[:]
        s = [None] * 4
        for i in range(len(s)):
            s[i] = Signal(i)
        s[1].next # read access
        s[2].next = 1
        s[2].next
        s[3].next = 0
        s[3].next = 1
        s[3].next = 3
        for i in range(len(s)):
            self.assertEqual(_siglist.count(s[i]), i)
            
    
class TestSignalAsNum(TestCase):

    def seqSetup(self, imin, imax, jmin=0, jmax=None):
        seqi = [imin, imin,   12, 34]
        seqj = [jmin, 12  , jmin, 34]
        if not imax and not jmax:
            l = 2222222222222222222222222222
            seqi.append(l)
            seqj.append(l)
        # first some smaller ints
        for n in range(100):
            ifirstmax = jfirstmax = 100000
            if imax:
                ifirstmax = min(imax, ifirstmax)
            if jmax:
                jfirstmax = min(jmax, jfirstmax)
            i = randrange(imin, ifirstmax)
            j = randrange(jmin, jfirstmax)
            seqi.append(i)
            seqj.append(j)
        # then some potentially longs
        for n in range(100):
            if not imax:
                i = randrange(maxint) + randrange(maxint)
            else:
                i = randrange(imin, imax)
            if not jmax:
                j = randrange(maxint) + randrange(maxint)
            else:
                j = randrange(jmin, jmax)
            seqi.append(i)
            seqj.append(j)
        self.seqi = seqi
        self.seqj = seqj
        
    def binaryCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bi = Signal(long(i))
            bj = Signal(long(j))
            ref = op(long(i), j)
            r1 = op(bi, j)
            r2 = op(long(i), bj)
            r3 = op(bi, bj)
            self.assertEqual(type(r1), type(ref))
            self.assertEqual(type(r2), type(ref))
            self.assertEqual(type(r3), type(ref))
            self.assertEqual(r1, ref)
            self.assertEqual(r2, ref)
            self.assertEqual(r3, ref)

    def augmentedAssignCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bj = Signal(j)
            ref = long(i)
            ref = op(ref, j)
            r1 = bi1 = Signal(i)
            try:
                r1 = op(r1, j)
            except TypeError:
                pass
            else:
                self.fail()
            r2 = long(i)
            r2 = op(r2, bj)
            r3 = bi3 = Signal(i)
            try:
                r3 = op(r3, bj)
            except TypeError:
                pass
            else:
                self.fail()
            self.assertEqual(r2, ref)
            
    def unaryCheck(self, op, imin=0, imax=None):
        self.seqSetup(imin=imin, imax=imax)
        for i in self.seqi:
            bi = Signal(i)
            ref = op(i)
            r1 = op(bi)
            self.assertEqual(type(r1), type(ref))
            self.assertEqual(r1, ref)
            
    def conversionCheck(self, op, imin=0, imax=None):
        self.seqSetup(imin=imin, imax=imax)
        for i in self.seqi:
            bi = Signal(i)
            ref = op(i)
            r1 = op(bi)
            self.assertEqual(type(r1), type(ref))
            self.assertEqual(r1, ref)
            
    def comparisonCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bi = Signal(i)
            bj = Signal(j)
            ref = op(i, j)
            r1 = op(bi, j)
            r2 = op(i, bj)
            r3 = op(bi, bj)
            self.assertEqual(r1, ref)
            self.assertEqual(r2, ref)
            self.assertEqual(r3, ref)

    def testAdd(self):
        self.binaryCheck(operator.add)

    def testSub(self):
        self.binaryCheck(operator.sub)

    def testMul(self):
        self.binaryCheck(operator.mul, imax=maxint) # XXX doesn't work for long i???

    def testFloorDiv(self):
        self.binaryCheck(operator.floordiv, jmin=1)

    def testMod(self):
        self.binaryCheck(operator.mod, jmin=1)

    def testPow(self):
        self.binaryCheck(pow, jmax=64)

    def testLShift(self):
        self.binaryCheck(operator.lshift, jmax=256)

    def testRShift(self):
        self.binaryCheck(operator.rshift, jmax=256)

    def testAnd(self):
        self.binaryCheck(operator.and_)

    def testOr(self):
        self.binaryCheck(operator.or_)

    def testXor(self):
        self.binaryCheck(operator.xor)

    def testIAdd(self):
        self.augmentedAssignCheck(operator.iadd)

    def testISub(self):
        self.augmentedAssignCheck(operator.isub)

    def testIMul(self):
        self.augmentedAssignCheck(operator.imul, imax=maxint) #XXX doesn't work for long i???

    def testIFloorDiv(self):
        self.augmentedAssignCheck(operator.ifloordiv, jmin=1)

    def testIMod(self):
        self.augmentedAssignCheck(operator.imod, jmin=1)

    def testIPow(self):
        self.augmentedAssignCheck(operator.ipow, jmax=64)

    def testIAnd(self):
        self.augmentedAssignCheck(operator.iand)

    def testIOr(self):
        self.augmentedAssignCheck(operator.ior)

    def testIXor(self):
        self.augmentedAssignCheck(operator.ixor)

    def testILShift(self):
        self.augmentedAssignCheck(operator.ilshift, jmax=256)

    def testIRShift(self):
        self.augmentedAssignCheck(operator.irshift, jmax=256)

    def testNeg(self):
        self.unaryCheck(operator.neg)
        
    def testNeg(self):
        self.unaryCheck(operator.pos)

    def testAbs(self):
        self.unaryCheck(operator.abs)

    def testInvert(self):
        self.unaryCheck(operator.inv)

    def testInt(self):
        self.conversionCheck(int, imax=maxint)
        
    def testLong(self):
        self.conversionCheck(long)
        
    def testFloat(self):
        self.conversionCheck(float)

    # XXX __complex__ seems redundant ??? (complex() works as such?)
  
    def testOct(self):
        self.conversionCheck(oct)
        
    def testHex(self):
        self.conversionCheck(hex)

    def testLt(self):
        self.comparisonCheck(operator.lt)
    def testLe(self):
        self.comparisonCheck(operator.le)
    def testGt(self):
        self.comparisonCheck(operator.gt)
    def testGe(self):
        self.comparisonCheck(operator.ge)
    def testEq(self):
        self.comparisonCheck(operator.eq)
    def testNe(self):
        self.comparisonCheck(operator.ne)


def getItem(s, i):
    ext = '0' * (i-len(s)+1)
    exts = ext + s
    si = len(exts)-1-i
    return exts[si]

def getSlice(s, i, j):
    ext = '0' * (i-len(s)+1)
    exts = ext + s
    si = len(exts)-i
    sj = len(exts)-j
    return exts[si:sj]



class TestSignalIntBvIndexing(TestCase):

    def seqsSetup(self):
        seqs = ["0", "1", "000", "111", "010001", "110010010", "011010001110010"]
        seqs.extend(["0101010101", "1010101010", "00000000000", "11111111111111"])
        seqs.append("11100101001001101000101011011101001101")
        seqs.append("00101011101001011111010100010100100101010001001")
        self.seqs = seqs
        seqv = ["0", "1", "10", "101", "1111", "1010"]
        seqv.extend(["11001", "00111010", "100111100"])
        seqv.append("0110101001111010101110011010011")
        seqv.append("1101101010101101010101011001101101001100110011")
        self.seqv = seqv

    def testGetItem(self):
        self.seqsSetup()
        for s in self.seqs:
            n = long(s, 2)
            sbv = Signal(intbv(n))
            sbvi = Signal(intbv(~n))
            for i in range(len(s)+20):
                ref = long(getItem(s, i), 2)
                res = sbv[i]
                resi = sbvi[i]
                self.assertEqual(res, ref)
                self.assertEqual(type(res), bool)
                self.assertEqual(resi, ref^1)
                self.assertEqual(type(resi), bool)

    def testGetSlice(self):
        self.seqsSetup()
        for s in self.seqs:
            n = long(s, 2)
            sbv = Signal(intbv(n))
            sbvi = Signal(intbv(~n))
            for i in range(1, len(s)+20):
                for j in range(0,len(s)+20):
                    try:
                        res = sbv[i:j]
                        resi = sbvi[i:j]
                    except ValueError:
                        self.assertTrue(i<=j)
                        continue
                    ref = long(getSlice(s, i, j), 2)
                    self.assertEqual(res, ref)
                    self.assertEqual(type(res), intbv)
                    mask = (2**(i-j))-1
                    self.assertEqual(resi, ref ^ mask)
                    self.assertEqual(type(resi), intbv)

    def testSetItem(self):
        sbv = Signal(intbv(5))
        try:
            sbv[1] = 1
        except TypeError:
            pass
        else:
            self.fail()
            
    def testSetSlice(self):
        sbv = Signal(intbv(5))
        try:
            sbv[1:0] = 1
        except TypeError:
            pass
        else:
            self.fail()


class TestSignalNrBits(TestCase):

    def testBool(self):
        if type(bool) is not type : # bool not a type in 2.2
            return
        s = Signal(bool())
        self.assertEqual(s._nrbits, 1)

    def testIntbvSlice(self):
        for n in range(1, 40):
            for m in range(0, n):
                s = Signal(intbv()[n:m])
                self.assertEqual(s._nrbits, n-m)

    def testIntbvBounds(self):
        for n in range(1, 40):
            s = Signal(intbv(min=-(2**n)))
            self.assertEqual(s._nrbits, 0)
            s = Signal(intbv(max=2**n))
            self.assertEqual(s._nrbits, 0)
            s = Signal(intbv(min=0, max=2**n))
            self.assertEqual(s._nrbits, n)
            s = Signal(intbv(1, min=1, max=2**n))
            self.assertEqual(s._nrbits, n)
            s = Signal(intbv(min=0, max=2**n+1))
            self.assertEqual(s._nrbits, n+1)
            s = Signal(intbv(min=-(2**n), max=2**n-1))
            self.assertEqual(s._nrbits, n+1)
            s = Signal(intbv(min=-(2**n), max=1))
            self.assertEqual(s._nrbits, n+1)
            s = Signal(intbv(min=-(2**n)-1, max=2**n-1))
            self.assertEqual(s._nrbits, n+2)
            

class TestSignalBoolBounds(TestCase):
    
    def testSignalBoolBounds(self):
        if type(bool) is not type: # bool not a type in 2.2
            return
        s = Signal(bool())
        s.next = 1
        s.next = 0
        for v in (-1, -8, 2, 5):
            try:
                s.next = v
                #s._update()
                #s.val
            except ValueError:
                pass
            else:
                self.fail()

                
class TestSignalIntbvBounds(TestCase):

    def testSliceAssign(self):
        s = Signal(intbv(min=-24, max=34))
        for i in (-24, -2, 13, 33):
            for k in (6, 9, 10):
                s.next[:] = 0
                s.next[k:] = i
                self.assertEqual(s.next, i)
        for i in (-25, -128, 34, 35, 229):
            for k in (0, 9, 10):
                try:
                    s.next[k:] = i
                    # s._update()
                except ValueError:
                    pass
                else:
                    self.fail()
        s = Signal(intbv(5)[8:])
        for v in (0, 2**8-1, 100):
            s.next[:] = v
        for v in (-1, 2**8, -10, 1000):
            try:
                s.next[:] = v
                # s._update()
            except ValueError:
                pass
            else:
                self.fail()
            

if __name__ == "__main__":
    unittest.main()
