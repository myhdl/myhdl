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

""" myhdl _extractHierarchy module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
from inspect import currentframe, getframeinfo, getouterframes
import re
import string
from types import GeneratorType
import compiler
from compiler import ast
import linecache
from sets import Set

from myhdl import Signal, ExtractHierarchyError
from myhdl._util import _isGenFunc
from myhdl._isGenSeq import _isGenSeq
from myhdl._always_comb import _AlwaysComb


_profileFunc = None
    
class _error:
    pass
_error.NoInstances = "No instances found"

re_assign = r"""^
                \s*
                (?P<name>\w[\w\d]*)
                (?P<index>\[.*\])?
                \s*
                =
                """
 
rex_assign = re.compile(re_assign, re.X)

_filelinemap = {}

_memInfoMap = {}

class _MemInfo(object):
    __slots__ = ['mem', 'name', 'elObj', 'depth', 'decl']
    def __init__(self, mem):
        self.mem = mem
        self.decl = True
        self.name = None
        self.depth = len(mem)
        self.elObj = mem[0]


def _getMemInfo(mem):
    return _memInfoMap[id(mem)]

def _makeMemInfo(mem):
    key = id(mem)
    if key not in _memInfoMap:
        _memInfoMap[key] = _MemInfo(mem)
    return _memInfoMap[key]
    
def _isMem(mem):
    return id(mem) in _memInfoMap

def _isListOfSigs(obj):
    if isinstance(obj, list):
        for e in obj:
            if not isinstance(e, Signal):
                return False
        return True
    else:
        return False

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
        
 

class _HierExtr(object):
    
    def __init__(self, name, dut, *args, **kwargs):
        
        global _profileFunc
        global _memInfoMap
        _memInfoMap = {}
        self.skipNames = ('always_comb', 'instances', 'processes')
        self.skip = 0
        self.hierarchy = hierarchy = []
        self.absnames = absnames = {}
        self.level = 0
        self.returned = Set()
        
        # handle special case of a top-level generator separately
        if _isGenFunc(dut):
            _top = dut(*args, **kwargs)
            gsigdict = {}
            gmemdict = {}
            for dict in (_top.gi_frame.f_globals, _top.gi_frame.f_locals):
                for n, v in dict.items():
                    if isinstance(v, Signal):
                        gsigdict[n] = v
                    if _isListOfSigs(v):
                        gmemdict[n] = _makeMemInfo(v)
            inst = [1, (_top, ()), gsigdict, gmemdict]
            self.hierarchy.append(inst)
        # the normal case
        else:
            _profileFunc = self.extractor
            sys.setprofile(_profileFunc)
            _top = dut(*args, **kwargs)
            sys.setprofile(None)
            if not hierarchy:
                raise ExtractHierarchyError(_error.NoInstances)
            
        self.top = _top

        # streamline hierarchy
        hierarchy.reverse()
        # walk the hierarchy to define relative and absolute names
        # in this case, we'll use the names from the lowest levels
        names = {}
        obj, subs = hierarchy[0][1]
        names[id(obj)] = name
        absnames[id(obj)] = '_' + name
        for m in hierarchy:
            obj, subs = m[1]
            assert id(obj) in names
            tn = absnames[id(obj)]
            for sn, so in subs:
                names[id(so)] = sn
                absnames[id(so)] = "%s_%s" % (tn, sn)
                if isinstance(so, (tuple, list)):
                    for i, soi in enumerate(so):
                        names[id(soi)] = "%s[%s]" % (sn, i)
                        absnames[id(soi)] = "%s_%s_%s" % (tn, sn, i)
            m[1] = names[id(obj)]
           

                
    def extractor(self, frame, event, arg):
        
        if event == "call":
            
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 1
            if not self.skip:
                self.level += 1
                
        elif event == "return":
            
           if not self.skip:
                if _isGenSeq(arg):
                    sigdict = {}
                    memdict = {}
                    for dict in (frame.f_globals, frame.f_locals):
                        for n, v in dict.items():
                            if isinstance(v, Signal):
                                sigdict[n] = v
                            if _isListOfSigs(v):
                                memdict[n] = _makeMemInfo(v)
                    l = []
                    for n, o in frame.f_locals.items():
                        for e in _inferArgs(arg):
                            if e is o:
                                l.append((n, o))
                    for n, o in l:
                        if type(o) is _AlwaysComb:
                            g = o.gen
                        else:
                            g = o
                        # special handling of locally defined generators
                        # outside the profiling mechanism
                        if id(o) not in self.returned and \
                            type(g) is GeneratorType:
                            gsigdict = {}
                            gmemdict = {}
                            for dict in (g.gi_frame.f_globals,
                                         g.gi_frame.f_locals):
                                for n, v in dict.items():
                                    if isinstance(v, Signal):
                                        gsigdict[n] = v
                                    if _isListOfSigs(v):
                                        gmemdict[n] = _makeMemInfo(v)
                            inst = [self.level+1, (o, ()), gsigdict, gmemdict]
                            self.hierarchy.append(inst)
                    self.returned.add(id(arg))
                    inst = [self.level, (arg, l), sigdict, memdict]
                    self.hierarchy.append(inst)
                self.level -= 1
                
           func_name = frame.f_code.co_name
           if func_name in self.skipNames:
               self.skip = 0
                


def _getGens(arg):
    if type(arg) is GeneratorType:
        return [arg]
    elif type(arg) is _AlwaysComb:
        return [arg.gen]
    else:
        l = []
        for elt in arg:
            if type(elt) is GeneratorType:
                l.append(elt)
            elif type(elt) is _AlwaysComb:
                l.append(elt.gen)
        return l


def _inferArgs(arg):
    c = [arg]
    if isinstance(arg, (tuple, list)):
        c += list(arg)
    return c
   


    
    

            
        
    
    
