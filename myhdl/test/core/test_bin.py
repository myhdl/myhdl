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

""" Run the unit tests for bin """
import random
import sys
from random import randrange

from myhdl import bin

random.seed(1)  # random, but deterministic


SIZE = 100


def _int2bitstring(num):
    if num == 0:
        return '0'
    if abs(num) == 1:
        return '1'
    return _int2bitstring(num // 2) + _int2bitstring(num % 2)


def binref(num, width=0):
    """Return a binary string representation.

    num -- number to convert
    Optional parameter:
    width -- specifies the desired string (sign bit padding)
    """
    num = int(num)
    s = _int2bitstring(num)
    if width:
        pad = '0'
        if num < 0:
            pad = '1'
        return (width - len(s)) * pad + s
    return s


class TestBin:

    def testSmall(self):
        for i in range(-65, 65):
            assert bin(i) == binref(i)

    def testSmallWidth(self):
        for i in range(-65, 65):
            w = randrange(1, 8)
            assert bin(i, w) == binref(i, w)

    def testRandomInt(self):
        for j in range(SIZE):
            i = randrange(-sys.maxsize, sys.maxsize)
            assert bin(i) == binref(i)

    def testRandomIntWidth(self):
        for j in range(SIZE):
            w = randrange(1, 1000)
            i = randrange(-sys.maxsize, sys.maxsize)
            assert bin(i, w) == binref(i, w)

    def testRandomLong(self):
        for j in range(SIZE):
            k = randrange(sys.maxsize)
            i = k + sys.maxsize
            assert bin(i) == binref(i)
            i = -k - sys.maxsize
            assert bin(i) == binref(i)

    def testRandomLongWith(self):
        for j in range(SIZE):
            w = randrange(1, 1000)
            k = randrange(sys.maxsize)
            i = k + sys.maxsize
            assert bin(i, w) == binref(i, w)
            i = -k - sys.maxsize
            assert bin(i, w) == binref(i, w)
