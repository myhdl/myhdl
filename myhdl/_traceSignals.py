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
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" myhdl traceSignals module.

"""
from __future__ import absolute_import
from __future__ import print_function



import sys
from inspect import currentframe, getouterframes
import time
import os
path = os.path
import shutil

from myhdl import _simulator, __version__, EnumItemType
from myhdl._extractHierarchy import _HierExtr
from myhdl import TraceSignalsError
from myhdl._ShadowSignal import _TristateSignal, _TristateDriver

_tracing = 0
_profileFunc = None

class _error:
    pass
_error.TopLevelName = "result of traceSignals call should be assigned to a top level name"
_error.ArgType = "traceSignals first argument should be a classic function"
_error.MultipleTraces = "Cannot trace multiple instances simultaneously"


class _TraceSignalsClass(object):

    __slot__ = ("name",
                "timescale",
                "tracelists"
                )

    def __init__(self):
        self.name = None
        self.timescale = "1ns"
        self.tracelists = True

    def __call__(self, dut, *args, **kwargs):
        global _tracing
        if _tracing:
            return dut(*args, **kwargs) # skip
        else:
            # clean start
            sys.setprofile(None)
        from myhdl.conversion import _toVerilog
        if _toVerilog._converting:
            raise TraceSignalsError("Cannot use traceSignals while converting to Verilog")
        if not callable(dut):
            raise TraceSignalsError(_error.ArgType, "got %s" % type(dut))
        if _simulator._tracing:
            raise TraceSignalsError(_error.MultipleTraces)

        _tracing = 1
        try:
            if self.name is None:
                name = dut.__name__
            else:
                name = str(self.name)
            if name is None:
                raise TraceSignalsError(_error.TopLevelName)
            h = _HierExtr(name, dut, *args, **kwargs)
            vcdpath = name + ".vcd"
            if path.exists(vcdpath):
                backup = vcdpath + '.' + str(path.getmtime(vcdpath))
                shutil.copyfile(vcdpath, backup)
                os.remove(vcdpath)
            vcdfile = open(vcdpath, 'w')
            _simulator._tracing = 1
            _simulator._tf = vcdfile
            _writeVcdHeader(vcdfile, self.timescale)
            _writeVcdSigs(vcdfile, h.hierarchy, self.tracelists)
        finally:
            _tracing = 0

        return h.top

traceSignals = _TraceSignalsClass()


_codechars = ""
for i in range(33, 127):
    _codechars += chr(i)
_mod = len(_codechars)

def _genNameCode():
    n = 0
    while 1:
        yield _namecode(n)
        n += 1
        
def _namecode(n):
    q, r = divmod(n, _mod)
    code = _codechars[r]
    while q > 0:
        q, r = divmod(q, _mod)
        code = _codechars[r] + code
    return code

def _writeVcdHeader(f, timescale):
    print("$date", file=f)
    print("    %s" % time.asctime(), file=f)
    print("$end", file=f)
    print("$version", file=f)
    print("    MyHDL %s" % __version__, file=f)
    print("$end", file=f)
    print("$timescale", file=f)
    print("    %s" % timescale, file=f)
    print("$end", file=f)
    print(file=f)

def _getSval(s):
    if isinstance(s, _TristateSignal):
        sval = s._orival
    elif isinstance(s, _TristateDriver):
        sval = s._sig._orival
    else:
        sval = s._val
    return sval

def _writeVcdSigs(f, hierarchy, tracelists):
    curlevel = 0
    namegen = _genNameCode()
    siglist = []
    for inst in hierarchy:
        level = inst.level
        name = inst.name
        sigdict = inst.sigdict
        memdict = inst.memdict
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta >= 0:
            for i in range(delta + 1):
                print("$upscope $end", file=f)
        print("$scope module %s $end" % name, file=f)
        for n, s in sigdict.items():
            sval = _getSval(s)
            if sval is None:
                raise ValueError("%s of module %s has no initial value" % (n, name))
            if not s._tracing:
                s._tracing = 1
                s._code = next(namegen)
                siglist.append(s)
            w = s._nrbits
            # use real for enum strings
            if w and not isinstance(sval, EnumItemType):
                if w == 1:
                    print("$var reg 1 %s %s $end" % (s._code, n), file=f)
                else:
                    print("$var reg %s %s %s $end" % (w, s._code, n), file=f)
            else:
                print("$var real 1 %s %s $end" % (s._code, n), file=f)
        # Memory dump by Frederik Teichert, http://teichert-ing.de, date: 2011.03.28
        # The Value Change Dump standard doesn't support multidimensional arrays so 
        # all memories are flattened and renamed.
        if tracelists:
            for n in memdict.keys():
                memindex = 0
                for s in memdict[n].mem:
                    sval = _getSval(s)
                    if sval is None:
                        raise ValueError("%s of module %s has no initial value" % (n, name))
                    if not s._tracing:
                        s._tracing = 1
                        s._code = next(namegen)
                        siglist.append(s)
                    w = s._nrbits
                    if w:
                        if w == 1:
                            print("$var reg 1 %s %s(%i) $end" % (s._code, n, memindex), file=f)
                        else:
                            print("$var reg %s %s %s(%i) $end" % (w, s._code, n, memindex), file=f)
                    else:
                        print("$var real 1 %s %s(%i) $end" % (s._code, n, memindex), file=f)
                    memindex += 1
    for i in range(curlevel):
        print("$upscope $end", file=f)
    print(file=f)
    print("$enddefinitions $end", file=f)
    print("$dumpvars", file=f)
    for s in siglist:
        s._printVcd() # initial value
    print("$end", file=f)
            
            
        
        


    
    

            
        
    
    
