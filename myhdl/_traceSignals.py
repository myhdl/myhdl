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
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" myhdl traceSignals module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators

import sys
from inspect import currentframe, getframeinfo, getouterframes
import inspect
import re
import string
import time
from types import FunctionType
import os
path = os.path
import shutil
import compiler
from compiler import ast
import linecache

from myhdl import _simulator, Signal, __version__
from myhdl._util import _isGenSeq, _isgeneratorfunction

_tracing = 0
_profileFunc = None

class Error(Exception):
    """ traceSignals Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class TopLevelNameError(Error):
    """result of traceSignals call should be assigned to a top level name"""

class ArgTypeError(Error):
    """traceSignals first argument should be a classic function"""
    
class NoInstancesError(Error):
    """traceSignals returned no instances"""

class MultipleTracesError(Error):
    """Cannot trace multiple instances simultaneously"""

re_assign = r"""^
                \s*
                (?P<name>\w[\w\d]*)
                (?P<index>\[.*\])?
                \s*
                =
                """
 
rex_assign = re.compile(re_assign, re.X)


def traceSignals(dut, *args, **kwargs):
    global _tracing
    if _tracing:
        return dut(*args, **kwargs) # skip
    if not callable(dut):
        raise ArgTypeError("got %s" % type(dut))
    if _isgeneratorfunction(dut):
        raise ArgTypeError("got generator function")
    if _simulator._tracing:
        raise MultipleTracesError()
    _tracing = 1
    try:
        outer = getouterframes(currentframe())[1]
        name = _findInstanceName(outer)
        if name is None:
            raise TopLevelNameError
        h = _HierExtr(name, dut, *args, **kwargs)
        vcdpath = name + ".vcd"
        if path.exists(vcdpath):
            backup = vcdpath + '.' + str(path.getmtime(vcdpath))
            shutil.copyfile(vcdpath, backup)
            os.remove(vcdpath)
        vcdfile = open(vcdpath, 'w')
        _simulator._tracing = 1
        _simulator._tf = vcdfile
        _writeVcdHeader(vcdfile)
        _writeVcdSigs(vcdfile, h.hierarchy)
    finally:
        _tracing = 0
        linecache.clearcache()
    return h.m

_filelinemap = {}

class _CallFuncVisitor(object):

    def __init__(self):
        self.linemap = {}
    
    def visitAssign(self, node):
        if isinstance(node.expr, ast.CallFunc):
            self.lineno = None
            self.visit(node.expr)
            self.linemap[self.lineno] = node.lineno

    def visitName(self, node):
        self.lineno = node.lineno

def _findInstanceName(framerec):
    fr = framerec[0]
    fn = framerec[1]
    ln = framerec[2]
    if not _filelinemap.has_key(fn):
        tree = compiler.parseFile(fn)
        v = _CallFuncVisitor()
        compiler.walk(tree, v)
        linemap = _filelinemap[fn] = v.linemap
    else:
        linemap = _filelinemap[fn]
    if not linemap.has_key(ln):
        return None
    nln = linemap[ln]
    cl = linecache.getline(fn, nln)
    m = rex_assign.match(cl)
    name = None
    if m:
        basename, index = m.groups()
        if index:
            il = []
            for i in index[1:-1].split("]["):
                try:
                    s = str(eval(i, fr.f_globals, fr.f_locals))
                except:
                    break
                il.append(s)
            else:
                name = basename + '[' + "][".join(il) + ']'
        else:
            name = basename
    return name
 

class _HierExtr(object):
    
    def __init__(self, name, dut, *args, **kwargs):
        global _profileFunc
        self.skipNames = ('always_comb', 'instances', 'processes')
        self.skip = 0
        self.names = [name]
        self.hierarchy = hierarchy = []
        self.level = 0
        _profileFunc = self.extractor
        sys.setprofile(_profileFunc)
        try:
            _top = dut(*args, **kwargs)
        finally:
            sys.setprofile(None)
        if not hierarchy:
            raise NoInstancesError
        self.m = _top
        hierarchy.reverse()
        hierarchy[0][1] = name

    def extractor(self, frame, event, arg):
        if event == "call":
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 1
            if not self.skip:
                outer = getouterframes(frame)[1]
                name = _findInstanceName(outer)
                self.names.append(name)
                if name:
                    self.level += 1
        elif event == "return":
            if not self.skip:
                name = self.names.pop()
                if name:
                    if _isGenSeq(arg):
                        sigdict = {}
                        for dict in (frame.f_globals, frame.f_locals):
                            for n, v in dict.items():
                                if isinstance(v, Signal):
                                    sigdict[n] = v
                        i = [self.level, name, sigdict]
                        self.hierarchy.append(i)
                    self.level -= 1
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 0
          


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

def _writeVcdHeader(f):
    print >> f, "$date"
    print >> f, "    %s" % time.asctime()
    print >> f, "$end"
    print >> f, "$version"
    print >> f, "    MyHDL %s" % __version__
    print >> f, "$end"
    print >> f, "$timesscale"
    print >> f, "    1ns"
    print >> f, "$end"
    print >> f

def _writeVcdSigs(f, hierarchy):
    curlevel = 0
    namegen = _genNameCode()
    siglist = []
    for level, name, sigdict in hierarchy:
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta >= 0:
            for i in range(delta + 1):
                print >> f, "$upscope $end"
        print >> f, "$scope module %s $end" % name
        for n, s in sigdict.items():
            if not s._tracing:
                s._tracing = 1
                s._code = namegen.next()
                siglist.append(s)
            w = s._nrbits
            if w:
                if w == 1:
                    print >> f, "$var reg 1 %s %s $end" % (s._code, n)
                else:
                    print >> f, "$var reg %s %s %s $end" % (w, s._code, n)
            else:
                print >> f, "$var real 1 %s %s $end" % (s._code, n)
    for i in range(curlevel):
        print >> f, "$upscope $end"
    print >> f
    print >> f, "$enddefinitions $end"
    print >> f, "$dumpvars"
    for s in siglist:
        s._printVcd() # initial value
    print >> f, "$end"
            
            
        
        


    
    

            
        
    
    
