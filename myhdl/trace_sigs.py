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

""" myhdl trace_sigs module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators

import sys
from inspect import currentframe, getframeinfo, getouterframes
import compiler
import re
import string
import time
from types import FunctionType

from myhdl import _simulator, Signal, __version__
from myhdl.util import _isGenSeq, _isgeneratorfunction

_tracing = 0

class Error(Exception):
    """ trace_sigs Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class TopLevelNameError(Error):
    """result of trace_sigs call should be assigned to a top level name"""

class ArgTypeError(Error):
    """trace_sigs first argument should be a classic function"""
    
class NoInstancesError(Error):
    """trace_sigs returned no instances"""

re_assname = re.compile(r"^\s*(?P<assname>\w[\w\d]*)\s*=")

def trace_sigs(dut, *args, **kwargs):
    global _tracing
    if not callable(dut):
        raise ArgTypeError("got %s" % type(dut))
    if _isgeneratorfunction(dut):
        raise ArgTypeError("got generator function")
    if _tracing:
         return dut(*args, **kwargs) # skip
    _tracing = 1
    try:
        o = getouterframes(currentframe())[1]
        s = o[4][0]
        m = re_assname.match(s)
        name = None
        if m:
            name = m.group('assname')
        else:
            raise TopLevelNameError
        h = HierExtr(name, dut, *args, **kwargs)
        vcdfilename = name + ".vcd"
        vcdfile = open(vcdfilename, 'w')
        _simulator._tracing = 1
        _simulator._tf = vcdfile
        _writeVcdHeader(vcdfile)
        _writeVcdSigs(vcdfile, h.instances)
    finally:
        _tracing = 0
    return h.m
 

class HierExtr(object):
    
    def __init__(self, name, dut, *args, **kwargs):
        self.names = [name]
        self.instances = instances = []
        self.level = 0
        sys.setprofile(self.extractor)
        try:
            _top = dut(*args, **kwargs)
        finally:
            sys.setprofile(None)
        if not instances:
            raise NoInstancesError
        self.m = _top
        instances.reverse()
        # print instances
        instances[0][1] = name

    def extractor(self, frame, event, arg):
        if event == "call":
            o = getouterframes(frame)[1]
            s = o[4][0]
            m = re_assname.match(s)
            name = None
            if m:
                name = m.group('assname')
            self.names.append(name)
            if name:
               self.level += 1
        elif event == "return":
            name = self.names.pop()
            if name:
               if _isGenSeq(arg):
                  sigdict = {}
                  for dict in (frame.f_locals, frame.f_globals):
                      for n, v in dict.items():
                          if isinstance(v, Signal):
                              sigdict[n] = v
                  i = [self.level, name, sigdict]
                  self.instances.append(i)
               self.level -= 1


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

def _writeVcdSigs(f, instances):
    curlevel = 0
    namegen = _genNameCode()
    siglist = []
    for level, name, sigdict in instances:
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
                    print >> f, "$var reg %s %s %s $end" % (w, s.code, n)
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
            
            
        
        


    
    

            
        
    
    
