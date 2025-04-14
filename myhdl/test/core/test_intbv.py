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

""" Run the intbv unit tests. """
import operator
import random
import sys
from copy import copy, deepcopy
from random import randrange

import pytest

from myhdl import intbv

random.seed(2)  # random, but deterministic
maxint = sys.maxsize


class TestIntbvInit:

    def testDefaultValue(self):
        assert intbv() == 0


def getItem(s, i):
    ext = '0' * (i - len(s) + 1)
    exts = ext + s
    si = len(exts) - 1 - i
    return exts[si]


def getSlice(s, i, j):
    ext = '0' * (i - len(s) + 1)
    exts = ext + s
    si = len(exts) - i
    sj = len(exts) - j
    return exts[si:sj]


def getSliceLeftOpen(s, j):
    ext = '0' * (j - len(s) + 1)
    exts = ext + s
    if j:
        return exts[:-j]
    else:
        return exts


def setItem(s, i, val):
    ext = '0' * (i - len(s) + 1)
    exts = ext + s
    si = len(exts) - 1 - i
    return exts[:si] + val + exts[si + 1:]


def setSlice(s, i, j, val):
    ext = '0' * (i - len(s) + 1)
    exts = ext + s
    si = len(exts) - i
    sj = len(exts) - j
    return exts[:si] + val[si - sj:] + exts[sj:]


def setSliceLeftOpen(s, j, val):
    ext = '0' * (j - len(s) + 1)
    exts = ext + s
    if j:
        return val + exts[-j:]
    else:
        return val


class TestIntBvIndexing:

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
            n = int(s, 2)
            bv = intbv(n)
            bvi = intbv(~n)
            for i in range(len(s) + 20):
                ref = int(getItem(s, i), 2)
                res = bv[i]
                resi = bvi[i]
                assert res == ref
                assert type(res) == bool
                assert resi == ref ^ 1
                assert type(resi) == bool

    def testGetSlice(self):
        self.seqsSetup()
        for s in self.seqs:
            n = int(s, 2)
            bv = intbv(n)
            bvi = intbv(~n)
            for i in range(1, len(s) + 20):
                for j in range(0, len(s) + 20):
                    try:
                        res = bv[i:j]
                        resi = bvi[i:j]
                    except ValueError:
                        assert i <= j
                        continue
                    ref = int(getSlice(s, i, j), 2)
                    assert res == ref
                    assert type(res) == intbv
                    mask = (2 ** (i - j)) - 1
                    assert resi == ref ^ mask
                    assert type(resi) == intbv

    def testGetSliceLeftOpen(self):
        self.seqsSetup()
        for s in self.seqs:
            n = int(s, 2)
            bv = intbv(n)
            bvi = intbv(~n)
            for j in range(0, len(s) + 20):
                res = bv[:j]
                resi = bvi[:j]
                ref = int(getSliceLeftOpen(s, j), 2)
                assert res == ref
                assert type(res) == intbv
                assert resi + ref == -1
                assert type(res) == intbv

    def testSetItem(self):
        self.seqsSetup()
        for s in self.seqs:
            n = int(s, 2)
            for it in (int, intbv):
                for i in range(len(s) + 20):
                    # print i
                    bv0 = intbv(n)
                    bv1 = intbv(n)
                    bv0i = intbv(~n)
                    bv1i = intbv(~n)
                    bv0[i] = it(0)
                    bv1[i] = it(1)
                    bv0i[i] = it(0)
                    bv1i[i] = it(1)
                    ref0 = int(setItem(s, i, '0'), 2)
                    ref1 = int(setItem(s, i, '1'), 2)
                    ref0i = ~int(setItem(s, i, '1'), 2)
                    ref1i = ~int(setItem(s, i, '0'), 2)
                    assert bv0 == ref0
                    assert bv1 == ref1
                    assert bv0i == ref0i
                    assert bv1i == ref1i

    def testSetSlice(self):
        self.seqsSetup()
        toggle = 0
        for s in self.seqs:
            n = int(s, 2)
            for i in range(1, len(s) + 5):
                for j in range(0, len(s) + 5):
                    for v in self.seqv:
                        ext = '0' * (i - j - len(v))
                        extv = ext + v
                        bv = intbv(n)
                        bvi = intbv(~n)
                        val = int(v, 2)
                        toggle ^= 1
                        if toggle:
                            val = intbv(val)
                        try:
                            bv[i:j] = val
                        except ValueError:
                            assert i <= j or val >= 2 ** (i - j)
                            continue
                        else:
                            ref = int(setSlice(s, i, j, extv), 2)
                            assert bv == ref
                        mask = (2 ** (i - j)) - 1
                        vali = val ^ mask
                        try:
                            bvi[i:j] = vali
                        except ValueError:
                            assert vali >= 2 ** (i - j)
                            continue
                        else:
                            refi = ~int(setSlice(s, i, j, extv), 2)
                            assert bvi == refi

    def testSetSliceLeftOpen(self):
        self.seqsSetup()
        toggle = 0
        for s in self.seqs:
            n = int(s, 2)
            for j in range(0, len(s) + 5):
                for v in self.seqv:
                    bv = intbv(n)
                    bvi = intbv(~n)
                    val = int(v, 2)
                    toggle ^= 1
                    if toggle:
                        val = intbv(val)
                    bv[:j] = val
                    bvi[:j] = -1 - val
                    ref = int(setSliceLeftOpen(s, j, v), 2)
                    assert bv == ref
                    refi = ~int(setSliceLeftOpen(s, j, v), 2)
                    assert bvi == refi


class TestIntBvAsInt:

    def seqSetup(self, imin, imax, jmin=0, jmax=None):
        seqi = [imin, imin, 12, 34]
        seqj = [jmin, 12  , jmin, 34]
        if not imax and not jmax:
            l = 2222222222222222222222222222
            seqi.append(l)
            seqj.append(l)
        # first some smaller ints
        for __ in range(100):
            ifirstmax = jfirstmax = 100000
            if imax:
                ifirstmax = min(imax, ifirstmax)
            if jmax:
                jfirstmax = min(jmax, jfirstmax)
            i = randrange(imin, ifirstmax)
            j = randrange(jmin, jfirstmax)
            seqi.append(i)
            seqj.append(j)
        # then some potentially ints
        for __ in range(100):
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
            bi = intbv(int(i))
            bj = intbv(j)
            ref = op(int(i), j)
            r1 = op(bi, j)
            r2 = op(int(i), bj)
            r3 = op(bi, bj)
            # self.assertEqual(type(r1), intbv)
            # self.assertEqual(type(r2), intbv)
            # self.assertEqual(type(r3), intbv)
            assert r1 == ref
            assert r2 == ref
            assert r3 == ref

    def augmentedAssignCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bj = intbv(j)
            ref = int(i)
            ref = op(ref, j)
            r1 = bi1 = intbv(int(i))
            r1 = op(r1, j)
            r2 = int(i)
            r2 = op(r2, bj)
            r3 = bi3 = intbv(int(i))
            r3 = op(r3, bj)
            assert type(r1) == intbv
            assert type(r3) == intbv
            assert r1 == ref
            assert r2 == ref
            assert r3 == ref
            assert r1 is bi1
            assert r3 is bi3

    def unaryCheck(self, op, imin=0, imax=None):
        self.seqSetup(imin=imin, imax=imax)
        for i in self.seqi:
            bi = intbv(i)
            ref = op(i)
            r1 = op(bi)
            # self.assertEqual(type(r1), intbv)
            assert r1 == ref

    def conversionCheck(self, op, imin=0, imax=None):
        self.seqSetup(imin=imin, imax=imax)
        for i in self.seqi:
            bi = intbv(i)
            ref = op(i)
            r1 = op(bi)
            assert type(r1) == type(ref)
            assert r1 == ref

    def comparisonCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
        self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
        for i, j in zip(self.seqi, self.seqj):
            bi = intbv(i)
            bj = intbv(j)
            ref = op(i, j)
            r1 = op(bi, j)
            r2 = op(i, bj)
            r3 = op(bi, bj)
            assert r1 == ref
            assert r2 == ref
            assert r3 == ref

    def testAdd(self):
        self.binaryCheck(operator.add)

    def testSub(self):
        self.binaryCheck(operator.sub)

    def testMul(self):
        self.binaryCheck(operator.mul, imax=maxint)  # XXX doesn't work for long i???

    def testTrueDiv(self):
        self.binaryCheck(operator.truediv, jmin=1)

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
        self.augmentedAssignCheck(operator.imul, imax=maxint)  # XXX doesn't work for long i???

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

    def testPos(self):
        self.unaryCheck(operator.pos)

    def testAbs(self):
        self.unaryCheck(operator.abs)

    def testInvert(self):
        self.unaryCheck(operator.inv)

    def testInt(self):
        self.conversionCheck(int, imax=maxint)

    def testLong(self):
        self.conversionCheck(int)

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


class TestIntbvBounds:

    def testConstructor(self):
        assert intbv(40, max=54) == 40
        with pytest.raises(ValueError):
            intbv(40, max=27)

        assert intbv(25, min=16) == 25
        with pytest.raises(ValueError):
            intbv(25, min=27)

    def testSliceAssign(self):
        a = intbv(min=-24, max=34)
        for i in (-24, -2, 13, 33):
            for k in (6, 9, 10):
                a[:] = 0
                a[k:] = i
                assert a == i
        for i in (-25, -128, 34, 35, 229):
            for k in (0, 9, 10):
                with pytest.raises(ValueError):
                    a[k:] = i

        a = intbv(5)[8:]
        for v in (0, 2 ** 8 - 1, 100):
            a[:] = v
        for v in (-1, 2 ** 8, -10, 1000):
            with pytest.raises(ValueError):
                a[:] = v

    def checkBounds(self, i, j, op):
        a = intbv(i)
        assert a == i  # just to be sure
        try:
            exec("a %s int(j)" % op)
        except (ZeroDivisionError, ValueError):
            return  # prune
        if not isinstance(a._val, int):
            return  # prune
        if abs(a) > maxint * maxint:
            return  # keep it reasonable
        if a > i:
            b = intbv(i, min=i, max=a + 1)
            for m in (i + 1, a):
                b = intbv(i, min=i, max=m)
                with pytest.raises(ValueError):
                    exec("b %s int(j)" % op)
        elif a < i:
            b = intbv(i, min=a, max=i + 1)
            exec("b %s int(j)" % op)  # should be ok
            for m in (a + 1, i):
                b = intbv(i, min=m, max=i + 1)
                with pytest.raises(ValueError):
                    exec("b %s int(j)" % op)
        else:  # a == i
            b = intbv(i, min=i, max=i + 1)
            exec("b %s int(j)" % op)  # should be ok

    def checkOp(self, op):
        for i in (0, 1, -1, 2, -2, 16, -24, 129, -234, 1025, -15660):
            for j in (0, 1, -1, 2, -2, 9, -15, 123, -312, 2340, -23144):
                self.checkBounds(i, j, op)

    def testIAdd(self):
        self.checkOp("+=")

    def testISub(self):
        self.checkOp("-=")

    def testIMul(self):
        self.checkOp("*=")

    def testIFloorDiv(self):
        self.checkOp("//=")

    def testIMod(self):
        self.checkOp("%=")

    def testIPow(self):
        self.checkOp("**=")

    def testIAnd(self):
        self.checkOp("&=")

    def testIOr(self):
        self.checkOp("|=")

    def testIXor(self):
        self.checkOp("^=")

    def testILShift(self):
        self.checkOp("<<=")

    def testIRShift(self):
        self.checkOp(">>=")


class TestIntbvCopy:

    def testCopy(self):

        for n in (intbv(), intbv(34), intbv(-12, min=-15), intbv(45, max=65),
                  intbv(23, min=2, max=47), intbv(35)[3:]):
            a = intbv(n)
            b = copy(n)
            c = deepcopy(n)
            for m in (a, b, c):
                assert n == m
                assert n._val == m._val
                assert n.min == m.min
                assert n.max == m.max
                assert len(n) == len(m)


class TestIntbvIter:

    def testIter(self):

		n = intbv('01010001')
		values_iter = []
		values_rev = []
		for bit in n:
			values_iter.append(bit)
		for bit in reversed(n):
			values_rev.append(bit)
		assert values_iter == values_rev[::-1]

