#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003 Jan Decaluwe
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

""" Run unit tests for Cosimulation """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators
import sys
import os
import errno
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(1) # random, but deterministic

MAXLINE = 4096

from myhdl import Cosimulation, Error

class CosimulationTest(TestCase):

    exe = "python test_Cosimulation.py CosimulationTest"

    fromSigs = ['a', 'bb', 'ccc']
    fromSizes = [1, 11, 63]
    toSigs = ['d', 'ee', 'fff', 'g']
    toSizes = [32, 12, 3, 6]

    def testWrongExe(self):
        self.assertRaises(Error, Cosimulation, "bla -x 45")

    def testNotUnique(self):
        cosim1 = Cosimulation(self.exe + ".cosimNotUnique")
        self.assertRaises(Error, Cosimulation, self.exe + ".cosimNotUnique")

    def cosimNotUnique(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, "TO a")
        os.read(rf, MAXLINE)
        os.write(wt, "FROM d")
        os.read(rf, MAXLINE)
        os.write(wt, "0000")
        os.read(rf, MAXLINE)

    def testFromSignals(self):
        cosim = Cosimulation(self.exe + ".cosimFromSignals")
        self.assertEqual(cosim._fromSigs, self.fromSigs)
        self.assertEqual(cosim._fromSizes, self.fromSizes)
        self.assertEqual(cosim._toSigs, [])
        self.assertEqual(cosim._toSizes, [])

    def cosimFromSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM "
        for s, w in zip(self.fromSigs, self.fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "0000")
        os.read(rf, MAXLINE)

    def testToSignals(self):
        cosim = Cosimulation(self.exe + ".cosimToSignals")
        self.assertEqual(cosim._fromSigs, [])
        self.assertEqual(cosim._fromSizes, [])
        self.assertEqual(cosim._toSigs, self.toSigs)
        self.assertEqual(cosim._toSizes, self.toSizes)

    def cosimToSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO "
        for s, w in zip(self.toSigs, self.toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "0000")
        os.read(rf, MAXLINE)

    def testFromToSignals(self):
        cosim = Cosimulation(self.exe + ".cosimFromToSignals")
        self.assertEqual(cosim._fromSigs, self.fromSigs)
        self.assertEqual(cosim._fromSizes, self.fromSizes)
        self.assertEqual(cosim._toSigs, self.toSigs)
        self.assertEqual(cosim._toSizes, self.toSizes)

    def cosimFromToSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM "
        for s, w in zip(self.fromSigs, self.fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        buf = "TO "
        for s, w in zip(self.toSigs, self.toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "0000")
        os.read(rf, MAXLINE)
    
    def testTimeZero(self):
        self.assertRaises(Error, Cosimulation, self.exe + ".cosimTimeZero")

    def cosimTimeZero(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM "
        for s, w in zip(self.fromSigs, self.fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "0001")
        os.read(rf, MAXLINE)

    def testNoComm(self):
        self.assertRaises(Error, Cosimulation, self.exe + ".cosimNoComm")

    def cosimNoComm(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, "0000")
        os.read(rf, MAXLINE)
    


        

            
if __name__ == "__main__":
    unittest.main()

