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

from __future__ import generators

import sys
from inspect import currentframe, getframeinfo, getouterframes
import re
from types import GeneratorType
import compiler
from compiler import ast
import linecache
from sets import Set

from myhdl import Signal
from myhdl._util import _isGenSeq, _isGenFunc


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
    
class NoInstancesError(Error):
    """No instances found"""

re_assign = r"""^
                \s*
                (?P<name>\w[\w\d]*)
                (?P<index>\[.*\])?
                \s*
                =
                """
 
rex_assign = re.compile(re_assign, re.X)

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
        self.instNamesStack = [Set()]
        self.hierarchy = hierarchy = []
        self.level = 0
        # handle special case of a top-level generator separately
        if _isGenFunc(dut):
            _top = dut(*args, **kwargs)
            gsigdict = {}
            for dict in (_top.gi_frame.f_globals, _top.gi_frame.f_locals):
                for n, v in dict.items():
                    if isinstance(v, Signal):
                        gsigdict[n] = v
            inst = [1, name, gsigdict]
            self.hierarchy.append(inst)
        else:
            _profileFunc = self.extractor
            sys.setprofile(_profileFunc)
            try:
                _top = dut(*args, **kwargs)
            finally:
                sys.setprofile(None)
                if not hierarchy:
                    raise NoInstancesError
        self.top = _top
        hierarchy.reverse()
        hierarchy[0][1] = name
        linecache.clearcache()

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
                    self.instNamesStack[-1].add(name)
                    self.level += 1
                    self.instNamesStack.append(Set())
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
                        # check locally named generators
                        # those are not visited by the profiler mechanism
                        instNames = self.instNamesStack[-1]
                        gens = _getGens(arg)
                        for gname, g in frame.f_locals.items():
                            if type(g) is GeneratorType and \
                               g in gens and gname not in instNames:
                                gsigdict = {}
                                for dict in (g.gi_frame.f_globals,
                                             g.gi_frame.f_locals):
                                    for n, v in dict.items():
                                        if isinstance(v, Signal):
                                            gsigdict[n] = v
                                inst = [self.level+1, gname, gsigdict]
                                self.hierarchy.append(inst)
                        inst = [self.level, name, sigdict]       
                        self.hierarchy.append(inst)
                    self.level -= 1
                    self.instNamesStack.pop()
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 0
                

def _getGens(arg):
    if type(arg) is GeneratorType:
        return [arg]
    else:
        return [g for g in arg if type(g) is GeneratorType]


    


    
    

            
        
    
    
