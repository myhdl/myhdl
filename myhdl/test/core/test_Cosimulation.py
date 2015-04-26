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

""" Run unit tests for Cosimulation """
from __future__ import absolute_import


import sys
import os
import errno
import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(1) # random, but deterministic

MAXLINE = 4096

import pytest
from myhdl import Signal

from myhdl._Cosimulation import Cosimulation, CosimulationError, _error
from myhdl._compat import to_bytes, PYPY

exe = "python test_Cosimulation.py CosimulationTest"

fromSignames = ['a', 'bb', 'ccc']
fromSizes = [1, 11, 63]
fromVals = [0x2, 0x43, 0x24]
fromSigs = {}
for s, v in zip(fromSignames, fromVals):
    fromSigs[s] = Signal(v)
toSignames = ['d', 'ee', 'fff', 'g']
toSizes = [32, 12, 3, 6]
toSigs = {}
for s in toSignames:
    toSigs[s] = Signal(0)
toVals = [0x3, 0x45, 0x14, 0x12]
toXVals = ["X00", "FZ3", "34XZ", "56U"]
allSigs = fromSigs.copy()
allSigs.update(toSigs)

@pytest.mark.xfail(PYPY, reason="This test does not work on pypy")
class CosimulationTest(TestCase):
    
    def testWrongExe(self):
        try:
            Cosimulation("bla -x 45")
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.OSError)
        else:
            self.fail()

    def testNotUnique(self):
        cosim1 = Cosimulation(exe + ".cosimNotUnique", **allSigs)
        try:
            Cosimulation(exe + ".cosimNotUnique", **allSigs)
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.MultipleCosim)
        else:
            self.fail()

    def cosimNotUnique(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, b"TO 00 a 1")
        os.read(rf, MAXLINE)
        os.write(wt, b"FROM 00 d 1")
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
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
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        os.write(wt, b"TO 0000 a 1")
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
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
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        os.write(wt, b"FROM 0000")
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
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
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
        os.read(rf, MAXLINE)
    
    def testTimeZero(self):
        try:
            Cosimulation(exe + ".cosimTimeZero", **allSigs)
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.TimeZero)
        except:
            self.fail()

    def cosimTimeZero(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO 01 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, to_bytes(buf))

    def testNoComm(self):
        try:
            Cosimulation(exe + ".cosimNoComm", **allSigs)
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.NoCommunication)
        else:
            self.fail()
 
    def cosimNoComm(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        os.write(wt, b"FROM 0000")
        os.read(rf, MAXLINE)
        os.write(wt, b"TO 0000")
        os.read(rf, MAXLINE)
        os.write(wt, b"START ")
        os.read(rf, MAXLINE)

    def testFromSignalsDupl(self):
        try:
            Cosimulation(exe + ".cosimFromSignalsDupl", **allSigs)
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.DuplicateSigNames)
        else:
            self.fail()

    def cosimFromSignalsDupl(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        buf += "bb 5"
        os.write(wt, to_bytes(buf))

    def testToSignalsDupl(self):
        try:
            Cosimulation(exe + ".cosimToSignalsDupl", **allSigs)
        except CosimulationError as e:
            self.assertEqual(e.kind, _error.DuplicateSigNames)
        else:
            self.fail()
 
    def cosimToSignalsDupl(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        buf += "fff 6"
        os.write(wt, to_bytes(buf))

    def testFromSignalVals(self):
        cosim = Cosimulation(exe + ".cosimFromSignalVals", **allSigs)
        os.read(cosim._rt, MAXLINE)
        cosim._hasChange = 1
        cosim._put(0)

    def cosimFromSignalVals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        os.write(wt, b"TO 0000 a 1")
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
        os.read(rf, MAXLINE)
        os.write(wt, b"DUMMY")
        s = os.read(rf, MAXLINE)
        vals = [int(e, 16) for e in s.split()[1:]]
        self.assertEqual(vals, fromVals)

    def testToSignalVals(self):
        cosim = Cosimulation(exe + ".cosimToSignalVals", **allSigs)
        for n in toSignames:
            self.assertEqual(toSigs[n].next, 0)
        cosim._get()
        for n, v in zip(toSignames, toVals):
            self.assertEqual(toSigs[n].next, v)
        os.write(cosim._wf, b"DUMMY")
        cosim._getMode = 1
        cosim._get()
        for n in toSignames:
            self.assertEqual(toSigs[n].next, 0)
        

    def cosimToSignalVals(self):
        wt = int(os.environ['MYHDL_TO_PIPE'])
        rf = int(os.environ['MYHDL_FROM_PIPE'])
        buf = "FROM 00 "
        for s, w in zip(fromSignames, fromSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        buf = "TO 00 "
        for s, w in zip(toSignames, toSizes):
            buf += "%s %s " % (s, w)
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        os.write(wt, b"START")
        os.read(rf, MAXLINE)
        buf = "0 "
        for s, v in zip(toSignames, toVals):
            buf += s
            buf += " "
            buf += hex(v)[2:]
            buf += " "
        os.write(wt, to_bytes(buf))
        os.read(rf, MAXLINE)
        buf = "0 "
        for s, v in zip(toSignames, toXVals):
            buf += s
            buf += " "
            buf += v
            buf += " "
        os.write(wt, to_bytes(buf))

def suite():
    return unittest.makeSuite(CosimulationTest, 'test')
        
if __name__ == "__main__":
    unittest.main()

