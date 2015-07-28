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

import os
import random

import pytest

from myhdl import Signal, Simulation, _simulator, delay, instance, intbv
from myhdl._traceSignals import TraceSignalsError, _error, traceSignals
from helpers import raises_kind

random.seed(1)  # random, but deterministic
path = os.path


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


@pytest.yield_fixture
def vcd_dir(tmpdir):
    with tmpdir.as_cwd():
        yield tmpdir
    if _simulator._tracing:
        _simulator._tf.close()
        _simulator._tracing = 0


class TestTraceSigs:

    def testMultipleTraces(self, vcd_dir):
        with raises_kind(TraceSignalsError, _error.MultipleTraces):
            dut = top3()

    def testArgType1(self, vcd_dir):
        with raises_kind(TraceSignalsError, _error.ArgType):
            dut = traceSignals([1, 2])

    def testReturnVal(self, vcd_dir):
        from myhdl import ExtractHierarchyError
        from myhdl._extractHierarchy import _error
        kind = _error.InconsistentToplevel % (2, "dummy")
        with raises_kind(ExtractHierarchyError, kind):
            dut = traceSignals(dummy)

    def testHierarchicalTrace1(self, vcd_dir):
        p = "%s.vcd" % fun.__name__
        top()
        assert path.exists(p)

    def testHierarchicalTrace2(self, vcd_dir):
        pdut = "%s.vcd" % top.__name__
        psub = "%s.vcd" % fun.__name__
        dut = traceSignals(top)
        assert path.exists(pdut)
        assert not path.exists(psub)

    def testTristateTrace(self, vcd_dir):
        Simulation(topTristate()).run(100, quiet=QUIET)

    def testBackupOutputFile(self, vcd_dir):
        p = "%s.vcd" % fun.__name__
        dut = traceSignals(fun)
        Simulation(dut).run(1000, quiet=QUIET)
        _simulator._tf.close()
        _simulator._tracing = 0
        size = path.getsize(p)
        pbak = p + '.' + str(path.getmtime(p))
        assert not path.exists(pbak)
        dut = traceSignals(fun)
        _simulator._tf.close()
        _simulator._tracing = 0
        assert path.exists(p)
        assert path.exists(pbak)
        assert path.getsize(pbak) == size
        assert path.getsize(p) < size
