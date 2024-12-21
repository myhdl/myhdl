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

""" myhdl traceSignals block.

"""
import sys
import time
import os
path = os.path
import shutil
import warnings

from myhdl import _simulator, __version__, EnumItemType
from myhdl._extractHierarchy import _HierExtr
from myhdl import TraceSignalsError
from myhdl._ShadowSignal import _TristateSignal, _TristateDriver
from myhdl._block import _Block
from myhdl._getHierarchy import _getHierarchy

_tracing = 0
_profileFunc = None
vcdpath = ''


class _error:
    pass


_error.TopLevelName = "result of traceSignals call should be assigned to a top level name"
_error.ArgType = "traceSignals first argument should be a classic function"
_error.MultipleTraces = "Cannot trace multiple instances simultaneously"


class _TraceSignalsClass(object):

    __slot__ = ("name",
                "directory",
                "filename",
                "timescale",
                "tracelists",
                "tracebackup"
                )

    def __init__(self):
        self.name = None
        self.directory = None
        self.filename = None
        self.timescale = "1ns"
        self.tracelists = True
        self.tracebackup = True

    def __call__(self, dut, *args, **kwargs):
        global _tracing, vcdpath
        if isinstance(dut, _Block):
            # now we go bottom-up: so clean up and start over
            # TODO: consider a warning for the overruled block
            if _simulator._tracing:
                _simulator._tracing = 0
                _simulator._tf.close()
                os.remove(vcdpath)
        else: # deprecated
            if _tracing:
                return dut(*args, **kwargs)  # skip
            else:
                # clean start
                sys.setprofile(None)

        from myhdl.conversion import _toVerilog
        if _toVerilog._converting:
            raise TraceSignalsError("Cannot use traceSignals while converting to Verilog")
        if not isinstance(dut, _Block):
            if not callable(dut):
                raise TraceSignalsError(_error.ArgType, "got %s" % type(dut))
        if _simulator._tracing:
            raise TraceSignalsError(_error.MultipleTraces)

        _tracing = 1
        try:
            if self.name is None:
                name = dut.__name__
                if isinstance(dut, _Block):
                    name = dut.func.__name__
            else:
                name = str(self.name)
            if name is None:
                raise TraceSignalsError(_error.TopLevelName)

            if self.directory is None:
                directory = ''
            else:
                directory = self.directory

            if isinstance(dut, _Block):
                h = _getHierarchy(name, dut)
            else:
                warnings.warn(
                    "\n    traceSignals(): Deprecated usage: See http://dev.myhdl.org/meps/mep-114.html",
                    category=DeprecationWarning,
                    stacklevel=2,
                    )
                h = _HierExtr(name, dut, *args, **kwargs)

            if self.filename is None:
                filename = name
            else:
                filename = str(self.filename)

            vcdpath = os.path.join(directory, filename + ".vcd")

            if path.exists(vcdpath):
                if self.tracebackup:
                    backup = vcdpath[:-4] + '.' + str(path.getmtime(vcdpath)) + '.vcd'
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
    print(f"   {time.asctime(time.gmtime())} UTC", file=f)
    print("$end", file=f)
    print("$version", file=f)
    print(f"    MyHDL {__version__}", file=f)
    print("$end", file=f)
    print("$timescale", file=f)
    print(f"    {timescale}", file=f)
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
    previouslevel = 0
    namegen = _genNameCode()
    siglist = []
    indent = 2
    upscopestack = []
    prefixstack = []
    fullpathnames = []

    for inst in hierarchy:
        level = inst.level
        name = inst.name
        sigdict = inst.sigdict
        memdict = inst.memdict
        delta = previouslevel - level
        previouslevel = level

        if name is None:
            # an @block(skipname=True) has been applied for this 'inst'
            # Note that this will skip a level, so we should skip a matching 'upscope', the upscopestack helps in handling that
            pass
        else:
            assert(delta >= -1)
            # close previous 'downscopes'
            if delta >= 0:
                while upscopestack[-1] >= level:
                        indent -= 2
                        print(f"{' '*indent}$upscope $end", file=f)
                        upscopestack.pop(-1)
                        prefixstack.pop(-1)
            # now open the new 'scope'
            print(f"{' '*indent}$scope module {name} $end", file=f)
            upscopestack.append(level)
            prefixstack.append(name)
            indent += 2

        fullpathprefix = '_'.join(prefixstack)
        for n, s in sigdict.items():
            sval = _getSval(s)
            if sval is None:
                raise ValueError(f"{n} of module {name} has no initial value")
            if not s._tracing:
                s._tracing = 1
                s._code = next(namegen)
                siglist.append(s)
            w = s._nrbits
            n = n.replace('self_', '')
            fullpathname = '_'.join((fullpathprefix, n))
            if fullpathname not in fullpathnames:
                fullpathnames.append(fullpathname)
                if w:
                    ww = w
                    if isinstance(sval, EnumItemType):
                        # 18-04-2014 jb
                        #  it is an enum, and as Impulse doesn't know the awkward 'real' representation yet,
                        #  so let's 'degrade' it to a binary type
                        # 30-04-2014 jb
                        #  Impulse now has a 'string'type
                        #  print "30-04-2014 jb: Representing enum as string"  # leave a trace
                        # TODO: re-visit string output in .vcd?
                        vcdtype = 'string'
                    else:
                        vcdtype = 'reg'
                else:
                    vcdtype = 'real'
                    ww = 1

                print(f"{' '*indent}$var {vcdtype} {ww} {s._code} {n} $end", file=f)

        # Memory dump by Frederik Teichert, http://teichert-ing.de, date: 2011.03.28
        # The Value Change Dump standard doesn't support multidimensional arrays so
        # all memories are flattened and renamed.
        if tracelists:
            for n in memdict.keys():
                nn = n.replace('self_', '')
                fullpathname = '_'.join((fullpathprefix, nn))
                if fullpathname not in fullpathnames:
                    fullpathnames.append(fullpathname)
                    print(f"{' '*indent}$scope module {nn} $end", file=f)
                    indent += 2
                    memindex = 0
                    for s in memdict[n].mem:
                        sval = _getSval(s)
                        if sval is None:
                            raise ValueError(f"{nn} of module {name} has no initial value")
                        if not s._tracing:
                            s._tracing = 1
                            s._code = next(namegen)
                            siglist.append(s)
                        w = s._nrbits
                        if w:
                            ww = w
                            if  isinstance(sval, EnumItemType):
                                # 03-02-20 jb
                                # Impulse has a 'string'type (since 2014, see above)
                                vcdtype = 'string'
                            else:
                                vcdtype = 'reg'
                        else:
                            vcdtype = 'real'
                            ww = 1

                        print(f"{' '*indent}$var {vcdtype} {ww} {s._code} {nn}({memindex}) $end", file=f)

                        memindex += 1
                    indent -= 2
                    print(f"{' '*indent}$upscope $end", file=f)

    # empty the upscope stack
    for __ in range(len(upscopestack)):
        indent -= 2
        print(f"{' '*indent}$upscope $end", file=f)

    print("\n$enddefinitions $end\n", file=f)
    print("$dumpvars", file=f)
    for s in siglist:
        s._printVcd()  # initial value
    print("$end", file=f)
