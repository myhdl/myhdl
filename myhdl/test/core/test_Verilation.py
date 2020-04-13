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

""" Run unit tests for Verilation """
from __future__ import absolute_import

import gc
import os
import sys
import shutil
import pytest

if sys.platform == "win32":
    import msvcrt

from myhdl import Signal, intbv, modbv, block, always, instance, delay, now, StopSimulation
from myhdl._Verilation import Verilation, VerilationError, _error

if __name__ != '__main__':
    from helpers import raises_kind


Verilator = True
try:
    import pyverilator
except:
    Verilator = False

class TestVerilation:
    def testNoArgs(self):
        with raises_kind(VerilationError, _error.AssertionError):
            Verilation(sofile='', top_verilog_file='')

    def testDoubleArgs(self):
        with raises_kind(VerilationError, _error.AssertionError):
            Verilation(sofile='a', top_verilog_file='b')


@pytest.mark.skipif(Verilator, reason='only needed when there is no (py)verilator')
class TestWithoutVerilation:
    def testPyVerilatorMissing(self):
        with raises_kind(VerilationError, _error.NoPyVerilator):
            Verilation(top_verilog_file='ttt.v')

from .top import tb_top

@pytest.mark.skipif(not Verilator, reason='no (py)verilator available')
class TestWithVerilation:

    def setup_method(self, method):
        gc.collect()

    def testVerilatorMissingFile(self):
        with raises_kind(VerilationError, _error.VerilatorError):
            Verilation(top_verilog_file='ttt.v')

    def testVerilatorVerilog(self):
        v = '''module ttp(); endmodule'''
        with open('ttp.v', 'w') as f:
            f.write(v)
        Verilation(top_verilog_file='ttp.v')
        # os.remove('ttp.v')
        # shutil.rmtree('obj_dir')

    def testVerilatorSharedLib(self):
        v = '''module ttp(); endmodule'''
        with open('ttp.v', 'w') as f:
            f.write(v)
        Verilation(sofile='obj_dir/Vttp')
        # os.remove('ttp.v')
        # shutil.rmtree('obj_dir')

    @pytest.mark.skip(reason='would start gtkwave gui probably fails in CI')
    def testVerilatorSharedLibTrace(self):
        v = '''module ttp(); endmodule'''
        with open('ttp.v', 'w') as f:
            f.write(v)
        Verilation(sofile='obj_dir/Vttp', trace=True, auto_tracing=False)
        # os.remove('ttp.v')
        # shutil.rmtree('obj_dir')

    def testVerilatorSignalTypes(self):
        tb = tb_top()
        tb.run_sim()
        ntb = tb_top(sim='verilator_vrl')
        ntb.run_sim()
        # os.remove('top.v')
        # shutil.rmtree('obj_dir')


if __name__ == "__main__":
    getattr(TestVerilation, sys.argv[1])()
    getattr(TestWithoutVerilation, sys.argv[1])()
    getattr(TestWithVerilation, sys.argv[1])()
