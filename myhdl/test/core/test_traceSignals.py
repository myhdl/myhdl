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

from myhdl import delay, Signal, Simulation, _simulator, instance
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
        for p in paths:
            os.remove(p)

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
        except TraceSignalsError, e:
            self.assertEqual(e.kind, _error.MultipleTraces)
        else:
            self.fail()

    def testArgType1(self):
        try:
            dut = traceSignals([1, 2])
        except TraceSignalsError, e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()

    def testReturnVal(self):
        from myhdl import ExtractHierarchyError
        from myhdl._extractHierarchy import _error
        try:
            dut = traceSignals(dummy)
        except ExtractHierarchyError, e:
            self.assertEqual(e.kind, _error.InconsistentToplevel % (2, "dummy"))
        else:
            self.fail()

    def testHierarchicalTrace1(self):
        p = "%s.vcd" % fun.func_name
        top()
        self.assert_(path.exists(p))

    def testHierarchicalTrace2(self):
        pdut = "%s.vcd" % top.func_name
        psub = "%s.vcd" % fun.func_name
        dut = traceSignals(top)
        self.assert_(path.exists(pdut))
        self.assert_(not path.exists(psub))

    def testBackupOutputFile(self):
        p = "%s.vcd" % fun.func_name
        dut = traceSignals(fun)
        Simulation(dut).run(1000, quiet=QUIET)
        _simulator._tf.close()
        _simulator._tracing = 0
        size = path.getsize(p)
        pbak = p + '.' + str(path.getmtime(p))
        self.assert_(not path.exists(pbak))
        dut = traceSignals(fun)
        _simulator._tf.close()
        _simulator._tracing = 0
        self.assert_(path.exists(p))
        self.assert_(path.exists(pbak))
        self.assert_(path.getsize(pbak) == size)
        self.assert_(path.getsize(p) < size)



if __name__ == "__main__":
    unittest.main()
