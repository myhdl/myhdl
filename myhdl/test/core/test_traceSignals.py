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

""" Run the unit tests for traceSignals """
from __future__ import absolute_import


import random
from random import randrange
random.seed(1) # random, but deterministic
import sys
import os
path = os.path

import unittest
from unittest import TestCase
import shutil
import glob

from myhdl import delay, intbv, Signal, Simulation, _simulator, instance
from myhdl._traceSignals import traceSignals, TraceSignalsError, _error

QUIET=1

def gen(clk):
    @instance
    def logic():
        while 1:
            yield delay(10)
            clk.next = not clk
    return logic

def fun():
    clk = Signal(bool(0))
    inst = gen(clk)
    return inst

def dummy():
    clk = Signal(bool(0))
    inst = gen(clk)
    return 1

def top():
    inst = traceSignals(fun)
    return inst

def top2():
    inst = [{} for i in range(4)]
    j = 3
    inst[j-2]['key'] = traceSignals(fun)
    return inst

def top3():
    inst_1 = traceSignals(fun)
    inst_2 = traceSignals(fun)
    return inst_1, inst_2


def genTristate(clk, x, y, z):
    xd = x.driver()
    yd = y.driver()
    zd = z.driver()

    @instance
    def ckgen():
        while 1:
            yield delay(10)
            clk.next = not clk
    @instance
    def logic():
        for v in [True, False, None, 0, True, None, None, 1]:
            yield clk.posedge
            xd.next = v
            if v is None:
                yd.next = zd.next = None
            elif v:
                yd.next = zd.next = 11
            else:
                yd.next = zd.next = 0
    return ckgen,logic

def tristate():
    from myhdl import TristateSignal
    clk = Signal(bool(0))
    x = TristateSignal(True)            # single bit
    y = TristateSignal(intbv(0))        # intbv with undefined width
    z = TristateSignal(intbv(0)[8:])    # intbv with fixed width

    inst = genTristate(clk, x, y, z)
    return inst

def topTristate():
    inst = traceSignals(tristate)
    return inst

class TestTraceSigs(TestCase):

    def setUp(self):
        paths = glob.glob("*.vcd") + glob.glob("*.vcd.*")
        for p in paths:
            os.remove(p)

    def tearDown(self):
        paths = glob.glob("*.vcd") + glob.glob("*.vcd.*")
        if _simulator._tracing:
            _simulator._tf.close()
            _simulator._tracing = 0
        #for p in paths:
        #    os.remove(p)

##     def testTopName(self):
##         p = "dut.vcd"
##         dut = traceSignals(fun)
##         _simulator._tf.close()
##         _simulator._tracing = 0
##         try:
##             traceSignals(fun)
##         except TraceSignalsError, e:
##             self.assertEqual(e.kind, _error.TopLevelName)
##         else:
##             self.fail()

    def testMultipleTraces(self):
        try:
            dut = top3()
        except TraceSignalsError as e:
            self.assertEqual(e.kind, _error.MultipleTraces)
        else:
            self.fail()

    def testArgType1(self):
        try:
            dut = traceSignals([1, 2])
        except TraceSignalsError as e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()

    def testReturnVal(self):
        from myhdl import ExtractHierarchyError
        from myhdl._extractHierarchy import _error
        try:
            dut = traceSignals(dummy)
        except ExtractHierarchyError as e:
            self.assertEqual(e.kind, _error.InconsistentToplevel % (2, "dummy"))
        else:
            self.fail()

    def testHierarchicalTrace1(self):
        p = "%s.vcd" % fun.__name__
        top()
        self.assertTrue(path.exists(p))

    def testHierarchicalTrace2(self):
        pdut = "%s.vcd" % top.__name__
        psub = "%s.vcd" % fun.__name__
        dut = traceSignals(top)
        self.assertTrue(path.exists(pdut))
        self.assertTrue(not path.exists(psub))

    def testTristateTrace(self):
        Simulation(topTristate()).run(100, quiet=QUIET)

    def testBackupOutputFile(self):
        p = "%s.vcd" % fun.__name__
        dut = traceSignals(fun)
        Simulation(dut).run(1000, quiet=QUIET)
        _simulator._tf.close()
        _simulator._tracing = 0
        size = path.getsize(p)
        pbak = p + '.' + str(path.getmtime(p))
        self.assertTrue(not path.exists(pbak))
        dut = traceSignals(fun)
        _simulator._tf.close()
        _simulator._tracing = 0
        self.assertTrue(path.exists(p))
        self.assertTrue(path.exists(pbak))
        self.assertTrue(path.getsize(pbak) == size)
        self.assertTrue(path.getsize(p) < size)



if __name__ == "__main__":
    unittest.main()
