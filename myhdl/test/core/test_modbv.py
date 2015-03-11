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

from myhdl._intbv import intbv
from myhdl._modbv import modbv

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
        

if __name__ == "__main__":
    unittest.main()
       
        
