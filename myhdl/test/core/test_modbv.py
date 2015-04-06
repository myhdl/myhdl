#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2011 Jan Decaluwe
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

""" Run the modbv unit tests. """
from __future__ import absolute_import

import unittest
from unittest import TestCase

import random
from random import randrange
random.seed(2) # random, but deterministic

import sys
maxint = sys.maxsize

from myhdl._intbv import intbv
from myhdl._modbv import modbv

import operator

class TestModbvWrap(TestCase):

    def testWrap(self):
        x = modbv(0, min=-8, max=8)
        x[:] = x + 1
        self.assertEqual(1, x)
        x[:] = x + 2
        self.assertEqual(3, x)
        x[:] = x + 5
        self.assertEqual(-8, x)
        x[:] = x + 1
        self.assertEqual(-7, x)
        x[:] = x - 5
        self.assertEqual(4, x)
        x[:] = x - 4
        self.assertEqual(0, x)
        x[:] += 15
        x[:] = x - 1
        self.assertEqual(-2, x)

    def testInit(self):
        self.assertRaises(ValueError, intbv, 15, min=-8, max=8)
        x = modbv(15, min=-8, max=8)
        self.assertEqual(-1, x)

        # Arbitrary boundraries support (no exception)
        modbv(5, min=-3, max=8)
        
    def testNoWrap(self):
        # Validate the base class fails for the wraps
        x = intbv(0, min=-8, max=8)
        try:
            x[:] += 15
            self.fail()
        except ValueError:
            pass

        x = intbv(0, min=-8, max=8)
        try:
            x[:] += 15
            self.fail()
        except ValueError:
            pass

class TestOps(TestCase):     
    def binaryCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bi = intbv(long(i))
            bj = intbv(j)
            ref = op(long(i), j)
            r1 = op(bi, j)
            r2 = op(long(i), bj)
            r3 = op(bi, bj)
            
            self.assertEqual(r1, ref)
            self.assertEqual(r2, ref)
            self.assertEqual(r3, ref)   

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

    def testAdd(self):
        self.binaryCheck(operator.add)

    def testSub(self):
        self.binaryCheck(operator.sub)

    def testMult(self):
        self.binaryCheck(operator.mul)

    def testTrueDiv(self):
        self.binaryCheck(operator.truediv, jmin=1)

    def testFloorDiv(self):
        self.binaryCheck(operator.floordiv, jmin=1)

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
  
if __name__ == "__main__":
    unittest.main()
       
        
