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

from myhdl import Signal

from Cosimulation import Cosimulation, \
     Error, \
     MultipleCosimError, \
     DuplicateSigNamesError, \
     SigNotFoundError, \
     TimeZeroError, \
     NoCommunicationError, \
     SimulationEndError

exe = "python test_Cosimulation.py CosimulationTest"

fromSignames = ['a', 'bb', 'ccc']
fromSizes = [1, 11, 63]
fromSigs = {}
for s in fromSignames:
    fromSigs[s] = Signal(0)
toSignames = ['d', 'ee', 'fff', 'g']
toSizes = [32, 12, 3, 6]
toSigs = {}
for s in toSignames:
    toSigs[s] = Signal(0)
allSigs = fromSigs.copy()
allSigs.update(toSigs)

class CosimulationTest(TestCase):
    
    def testWrongExe(self):
        self.assertRaises(Error, \
                          Cosimulation, "bla -x 45")

    def testNotUnique(self):
        cosim1 = Cosimulation(exe + ".cosimNotUnique", **allSigs)
        self.assertRaises(MultipleCosimError, 
                          Cosimulation, exe + ".cosimNotUnique", **allSigs)

    def cosimNotUnique(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, "TO 00 a 1")
        os.read(rf, MAXLINE)
        os.write(wt, "FROM 00 d 1")
        os.read(rf, MAXLINE)
        os.write(wt, "START")
        os.read(rf, MAXLINE)

    def testFromSignals(self):
        cosim = Cosimulation(exe + ".cosimFromSignals", **allSigs)
        self.assertEqual(cosim._fromSignames, fromSignames)
        self.assertEqual(cosim._fromSizes, fromSizes)

    def cosimFromSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "TO 0000 a 1")
        os.read(rf, MAXLINE)
        os.write(wt, "START")
        os.read(rf, MAXLINE)

    def testToSignals(self):
        cosim = Cosimulation(exe + ".cosimToSignals", **toSigs)
        self.assertEqual(cosim._fromSignames, [])
        self.assertEqual(cosim._fromSizes, [])
        self.assertEqual(cosim._toSignames, toSignames)
        self.assertEqual(cosim._toSizes, toSizes)

    def cosimToSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "FROM 0000")
        os.read(rf, MAXLINE)
        os.write(wt, "START")
        os.read(rf, MAXLINE)

    def testFromToSignals(self):
        cosim = Cosimulation(exe + ".cosimFromToSignals", **allSigs)
        self.assertEqual(cosim._fromSignames, fromSignames)
        self.assertEqual(cosim._fromSizes, fromSizes)
        self.assertEqual(cosim._toSignames, toSignames)
        self.assertEqual(cosim._toSizes, toSizes)

    def cosimFromToSignals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)
        os.read(rf, MAXLINE)
        os.write(wt, "START")
        os.read(rf, MAXLINE)
    
    def testTimeZero(self):
        self.assertRaises(TimeZeroError, \
                          Cosimulation, exe + ".cosimTimeZero", **allSigs)

    def cosimTimeZero(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO 01 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, buf)

    def testNoComm(self):
        self.assertRaises(NoCommunicationError, \
                          Cosimulation, exe + ".cosimNoComm", **allSigs)

    def cosimNoComm(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, "FROM 0000")
        os.read(rf, MAXLINE)
        os.write(wt, "TO 0000")
        os.read(rf, MAXLINE)
        os.write(wt, "START ")
        os.read(rf, MAXLINE)

    def testFromSignalsDupl(self):
        self.assertRaises(DuplicateSigNamesError, \
                          Cosimulation, exe + ".cosimFromSignalsDupl", **allSigs)

    def cosimFromSignalsDupl(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        buf += "bb 5"
        os.write(wt, buf)

    def testToSignalsDupl(self):
        self.assertRaises(DuplicateSigNamesError, \
                          Cosimulation, exe + ".cosimToSignalsDupl", **allSigs)
 
    def cosimToSignalsDupl(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        buf += "fff 6"
        os.write(wt, buf)

                   
if __name__ == "__main__":
    unittest.main()

