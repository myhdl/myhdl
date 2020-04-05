#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
#  Copyright (C) 2020 Jos Huisken
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

""" Module that provides the Verilation class

Verilation is a cosimulation method using the verilator.
No interprocvess communication is required, instead a C++ verilator library
of the verilog module  is dynamically loaded.

"""

from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import platform
try:
    import pyverilator
except ImportError as e:
    pass
from subprocess import CalledProcessError

#from myhdl.emulation.pinorder import Pinorder
from myhdl._intbv import intbv
from myhdl import _simulator, VerilationError
from myhdl._compat import set_inheritable, string_types, to_bytes, to_str
from myhdl._simulator import now

_MAXLINE = 4096
_DEVEL = True


class _error:
    pass
_error.NoPyVerilator = "No module pyverilator installed"
_error.NoVerilator = "No verilator available"
_error.MultipleVerilator = "Cannot load multiple verilators"
_error.SigNotFound = "Signal not found in Verilation arguments"
_error.NoCommunication = "No signals communicating to myhdl"
_error.VerilationEnd = "Premature verilation end"
_error.OSError = "OSError"
_error.AssertionError = "AssertionError"
_error.VerilatorError = "Verilator error"

class _debug:
    'Trace activity between verilator and myhdl while CoSimulating'
    count = 0
    def __init__(self, trcfile):
        try:
            self.ptrc = open(trcfile, 'w')
        except:
            self.ptrc = False
    def close(self):
        self.ptrc and self.ptrc.close()
        self.ptrc = False
    def write(self, s):
        self.ptrc and self.ptrc.write(s)

DBG = _debug('')
#DBG = _debug('verilator.trc')

class Verilation(object):

    """ Verilation class. """
    name = 'verilation_dut'

    def __init__(self, top_verilog_file='', sofile='', trace=False, auto_tracing = True, **kwargs):
        """ Construct an verilation object. """

        try:
            assert sofile or top_verilog_file, \
                'Either shared object "sofile" or "top_verilog_file" must be specified'
            assert not (sofile and top_verilog_file), \
                'Specified both shared object "%s" and top_verilog "%s" for verilation, using verilog' \
                % (sofile, top_verilog_file)
        except AssertionError as e:
            raise VerilationError(_error.AssertionError, str(e))

        try:
            if top_verilog_file:
                self.verilator = pyverilator.PyVerilator.build(top_verilog_file)
                self.verilator.auto_eval = False
            else:
                self.verilator = pyverilator.PyVerilator(sofile, auto_eval=False)
        except NameError as e:
            raise VerilationError(_error.NoPyVerilator)
        except AssertionError as e:
            raise VerilationError(_error.AssertionError, str(e))
        except CalledProcessError as e:
            raise VerilationError(_error.VerilatorError, str(e))
        except:
            raise VerilationError(_error.VerilatorError)

        if trace:
            if type(trace) == str:
                self.verilator.start_vcd_trace(trace, auto_tracing)
            self.verilator.start_gtkwave()
            self.verilator.send_to_gtkwave(self.verilator.io)
            self.verilator.send_to_gtkwave(self.verilator.internals)

        self._hasChange = 0
        self._getMode = 1

        self._toSigs = {}
        self._fromSigs = {}
        for s, S in self.verilator.all_signals.items():
            # print("s:", s, S, type(S))
            if type(S) == pyverilator.Output:
                self._toSigs[s[0]] = kwargs[s[0]]
            if type(S) == pyverilator.Input:
                self._fromSigs[s[0]] = kwargs[s[0]]

    def _get(self):
        if not self._getMode:
            return
        for s, sig in self._toSigs.items():
            # if sig._nrbits > 64:
            #     # sc_bv: (more then 64 bits) is array of uint32_t
            #     # print(self.verilator[s])
            #     next = self.verilator[s]
            #     # next = 0
            #     # for i in range((sig._nrbits - 1) // 32 + 1):
            #     #     next |= self.verilator[s][i] << (i * 32)
            # else:
            #     # either uint32_t or uint64_t
            #     next = self.verilator[s]
            if sig != self.verilator[s]:
                sig.next = self.verilator[s]
            DBG.write('%3d read- %s %s %s %s\n' % (now(), s, hex(self.verilator[s]), type(sig), sig))
        self._getMode = 0

    def _put(self, time):
        # self._hasChange = 1
        #print('V._put', self._hasChange, end=' ')
        #print('clk', self._fromSigs['clk'])
        if self._hasChange:
            self._hasChange = 0
            for s, sig in self._fromSigs.items():
                # if sig._nrbits > 64:
                #     # sc_bv: (more then 64 bits) is array of uint32_t
                #     v = []
                #     for i in range((sig._nrbits + 31) // 32):
                #         v.append((sig._val >> (i * 32)) & 0xffffffff)
                #     self.verilator[s] = v
                # else:
                #     # either uint32_t or uint64_t
                #     self.verilator[s] = int(sig._val)
                self.verilator[s] = int(sig._val)
                DBG.write('%3d writ- %s %s\n' % (now(), s, hex(sig._val)))
            self.verilator.eval()
        self._getMode = 1

    def _waiter(self):
        sigs = tuple(self._fromSigs.values())
        while 1:
            yield sigs
            self._hasChange = 1

    def __del__(self):
        """ Clear flag when this object destroyed - to suite unittest. """
        _simulator._verilate = 0
        DBG.close()
