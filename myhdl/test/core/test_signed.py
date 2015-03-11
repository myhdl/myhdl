#!/usr/bin/env python
#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2008 Jan Decaluwe
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

""" Run the intbv.signed() unit tests. """
from __future__ import absolute_import

import unittest
from unittest import TestCase

from random import randrange

from myhdl import *


class TestIntbvSigned(TestCase):
    '''Test cases to verify the intbv.signed() member function'''

    def testPlainIntbvInstance(self):
        '''Test a plain intbv instance with .signed() 

        ----+----+----+----+----+----+----+----
           -3   -2   -1    0    1    2    3

                          min  max
                               min  max
                     min       max
                     min            max
                min            max
                min       max
                min  max
              neither min nor max is set
              only max is set
              only min is set

        '''
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # in the following cases the .signed() function should classify the
        # value of the intbv instance as unsigned and return the 2's
        # complement value of the bits as specified by _nrbits.
        #

        # intbv with positive range, pos number, and msb not set, return signed()
        # Expect the number to be returned
        a = intbv(0x3b, min=0, max=0x7c)
        b = a.signed()
        self.assertEqual(b, 0x3b)

        # intbv with positive range, pos number, and msb set, return signed()
        # test various bit patterns to see that the 2's complement
        # conversion works correct
        # Expect the number to be converted to a negative number
        a = intbv(7, min=0, max=8)
        b = a.signed()
        self.assertEqual(b, -1)

        a = intbv(6, min=0, max=8)
        b = a.signed()
        self.assertEqual(b, -2)

        a = intbv(5, min=0, max=8)
        b = a.signed()
        self.assertEqual(b, -3)

        # set bit #3 and increase the range so that the set bit is considered
        # the sign bit. Here min = 0
        # Expect to return -4
        a = intbv(4, min=0, max=5)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=0, max=6)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=0, max=7)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=0, max=8)
        b = a.signed()
        self.assertEqual(b, -4)

        # here it is not the sign bit anymore
        # Expect the value to be 4
        a = intbv(4, min=0, max=9)
        b = a.signed()
        self.assertEqual(b, 4)

        # set bit #3 and increase the range so that the set bit is considered
        # the sign bit. Here min > 0
        # Expect to return -4
        a = intbv(4, min=1, max=5)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=2, max=6)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=3, max=7)
        b = a.signed()
        self.assertEqual(b, -4)

        a = intbv(4, min=4, max=8)
        b = a.signed()
        self.assertEqual(b, -4)

        # again with min > 0, here it is not the sign bit anymore
        # Expect the value to be 4
        a = intbv(4, min=2, max=9)
        b = a.signed()
        self.assertEqual(b, 4)

        # intbv with positive range, value = 0, return signed()
        # Expect the number to be returned
        a = intbv(0, min=0, max=0x8)
        b = a.signed()
        self.assertEqual(b, 0)


        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # in these cases the .signed() function should classify the
        # value of the intbv instance as signed and return the value as is
        #

        # intbv without range, pos number, return signed()
        # Expect value to be returned as is
        a = intbv(8)
        b = a.signed()
        self.assertEqual(b, 8)

        # intbv without range, neg number, return signed()
        # Expect value to be returned as is
        a = intbv(-8)
        b = a.signed()
        self.assertEqual(b, -8)

        # set bit #3 and increase the range that the set bit is actually the
        # msb, but due to the negative range not considered signed
        # Expect to return 4
        a = intbv(4, min=-1, max=5)
        b = a.signed()
        self.assertEqual(b, 4)

        a = intbv(4, min=-1, max=6)
        b = a.signed()
        self.assertEqual(b, 4)

        a = intbv(4, min=-1, max=7)
        b = a.signed()
        self.assertEqual(b, 4)

        a = intbv(4, min=-1, max=8)
        b = a.signed()
        self.assertEqual(b, 4)

        # intbv with negative range, pos number, and msb set, return signed()
        # Expect the number to returned as is
        a = intbv(7, min=-1, max=8)
        b = a.signed()
        self.assertEqual(b, 7)

        a = intbv(6, min=-1, max=8)
        b = a.signed()
        self.assertEqual(b, 6)

        a = intbv(5, min=-1, max=8)
        b = a.signed()
        self.assertEqual(b, 5)


        # intbv with symmetric (min = -max) range, pos value, msb set
        # return signed()
        # Expect value returned as is
        a = intbv(4, min=-8, max=8)
        b = a.signed()
        self.assertEqual(b, 4)

        # intbv with symmetric (min = -max) range, neg value,
        # return signed()
        # Expect value returned as is
        a = intbv(-4, min=-8, max=8)
        b = a.signed()
        self.assertEqual(b, -4)

        # intbv with symmetric (min=-max) range, value = 0,
        # return signed()
        # Expect value returned as is
        a = intbv(0, min=-8, max=8)
        b = a.signed()
        self.assertEqual(b, 0)


  
    def testSlicedSigned(self):
        '''Test a slice with .signed()

        This test can actually be simplified, as a slice will always have
        min=0 and max > min, which will result in an intbv instance that
        will be considered unsigned by the intbv.signed() function.
        '''
        a = intbv(4, min=-8, max=8)
        b = a[4:]
        self.assertEqual(b, 4)
        b = a[4:].signed()
        self.assertEqual(b, 4)    # msb is not set with a 4 bit slice

        b = a[3:]
        self.assertEqual(b, 4)
        b = a[3:].signed()
        self.assertEqual(b, -4)   # msb is set with 3 bits sliced


    def testSignedConcat(self):
        '''Test the .signed() function with the concatenate function'''

        # concat 3 bits
        # Expect the signed function to return a negative value
        a = concat(True, True, True).signed()
        self.assertEqual(a, -1)

        # concate a 3 bit intbv with msb set and two bits
        # Expect a negative number
        b = concat(intbv(5,min=0,max=8), True, True).signed()
        self.assertEqual(b, -9)


    def checkInvariants(self, a):
        """Check invariants of signed operator."""
        W = len(a)
        b = intbv(a.signed())
        if W > 0:
            self.assertEqual(a[W:], b[W:])
            self.assertEqual(b[:W], -a[W-1])
        else:
            self.assertEqual(a, b)

    def testRandom(self):
        NRTESTS = 1000
        for L in (10, 1000, 2**32, 2**68):
            for i in range(NRTESTS):
                lo = randrange(-L, L)
                hi = randrange(lo+1, 2*L)
                v = randrange(lo, hi)
                a = intbv(v, min=lo, max=hi)
                self.checkInvariants(a)
                self.checkInvariants(Signal(a))
    


########################################################################
# main
#
if __name__ == "__main__":
    unittest.main()
