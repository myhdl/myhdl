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
import inspect
from inspect import currentframe, getframeinfo, getouterframes
import re
import string
from types import GeneratorType
import compiler
from compiler import ast
import linecache
from sets import Set

from myhdl import Signal, ExtractHierarchyError, ToVerilogError, ToVHDLError
from myhdl._util import _isGenFunc
from myhdl._isGenSeq import _isGenSeq
from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always


_profileFunc = None
    
class _error:
    pass
_error.NoInstances = "No instances found"


class _Instance(object):
    __slots__ = ['level', 'obj', 'subs', 'sigdict', 'memdict', 'name']
    def __init__(self, level, obj, subs, sigdict, memdict):
        self.level = level
        self.obj = obj
        self.subs = subs
        self.sigdict = sigdict
        self.memdict = memdict
        

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

_userCodeMap = {'verilog' : {},
                'vhdl' : {}
               }

class _UserCode(object):
    __slots__ = ['code', 'namespace', 'sourcefile', 'funcname', 'sourceline']
    def __init__(self, code, namespace, sourcefile, funcname, sourceline):
        self.code = code
        self.namespace = namespace
        self.sourcefile = sourcefile
        self.funcname = funcname
        self.sourceline = sourceline

    def __str__(self):
        try:
            code = self.code % self.namespace
        except:
            type, value, tb = sys.exc_info()
            info = "in file %s, function %s starting on line %s:\n    " % \
                   (self.sourcefile, self.funcname, self.sourceline)
            msg = "%s: %s" % (type, value)
            self.raiseError(msg, info)
        code = "\n%s\n" % code
        return code

class _UserVerilog(_UserCode):
    def raiseError(self, msg, info):
        raise ToVerilogError("Error in user defined Verilog code", msg, info)
    
class _UserVhdl(_UserCode):
    def raiseError(self, msg, info):
        raise ToVHDLError("Error in user defined VHDL code", msg, info)

def _addUserCode(hdl, arg, code, namespace, sourcefile, funcname, sourceline):
    classMap = {'verilog' : _UserVerilog,
                'vhdl' :_UserVhdl
               }
    assert id(arg) not in _userCodeMap[hdl]
    _userCodeMap[hdl][id(arg)] = classMap[hdl](code, namespace, sourcefile, funcname, sourceline)
        

def _isListOfSigs(obj):
    """ Check if obj is a non-empty list of signals. """
    if isinstance(obj, list) and len(obj) > 0:
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
        _memInfoMap.clear()
        for hdl in _userCodeMap:
            _userCodeMap[hdl].clear()
        self.skipNames = ('always_comb', 'always', '_always_decorator', 'instance', \
                          'instances', 'processes', 'posedge', 'negedge')
        self.skip = 0
        self.hierarchy = hierarchy = []
        self.absnames = absnames = {}
        self.level = 0

        _profileFunc = self.extractor
        sys.setprofile(_profileFunc)
        _top = dut(*args, **kwargs)
        sys.setprofile(None)
        if not hierarchy:
            raise ExtractHierarchyError(_error.NoInstances)
            
        self.top = _top

        # streamline hierarchy
        hierarchy.reverse()
##         from pprint import pprint
##         pprint(hierarchy)
        # walk the hierarchy to define relative and absolute names
        names = {}
        top_inst = hierarchy[0]
        obj, subs = top_inst.obj, top_inst.subs
        names[id(obj)] = name
        absnames[id(obj)] = name
        for inst in hierarchy:
            obj, subs = inst.obj, inst.subs
            assert id(obj) in names
            inst.name = names[id(obj)]
            tn = absnames[id(obj)]
            for sn, so in subs:
                names[id(so)] = sn
                absnames[id(so)] = "%s_%s" % (tn, sn)
                if isinstance(so, (tuple, list)):
                    for i, soi in enumerate(so):
                        sni =  "%s_%s" % (sn, i)
                        names[id(soi)] = sni
                        absnames[id(soi)] = "%s_%s_%s" % (tn, sn, i)

                
    def extractor(self, frame, event, arg):
        
        if event == "call":
            
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 1
            if not self.skip:
                self.level += 1
                
        elif event == "return":
            
            if not self.skip:
                isGenSeq = _isGenSeq(arg)
                if isGenSeq:
                    for hdl in _userCodeMap:
                        key = "__%s__" % hdl
                        if key in frame.f_locals:
                            code = frame.f_locals[key]
                            namespace = frame.f_globals.copy()
                            namespace.update(frame.f_locals)
                            sourcefile = inspect.getsourcefile(frame)
                            funcname = frame.f_code.co_name
                            sourceline = inspect.getsourcelines(frame)[1]
                            _addUserCode(hdl, arg, code, namespace, sourcefile, funcname, sourceline)
                # building hierarchy only makes sense if there are generators
                if isGenSeq and arg:
                    sigdict = {}
                    memdict = {}
                    # print frame.f_code.co_cellvars
                    for dict in (frame.f_globals, frame.f_locals):
                        for n, v in dict.items():
                            if isinstance(v, Signal):
                                sigdict[n] = v
                            if _isListOfSigs(v):
                                memdict[n] = _makeMemInfo(v)
                    subs = []
                    for n, sub in frame.f_locals.items():
                        for elt in _inferArgs(arg):
                            if elt is sub:
                                subs.append((n, sub))
                                
                    inst = _Instance(self.level, arg, subs, sigdict, memdict)
                    self.hierarchy.append(inst)
                self.level -= 1
                
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 0
                


def _getGens(arg):
    if isinstance(arg, (GeneratorType, _AlwaysComb, _Always)):
        return [arg]
    else:
        gens = []
        for elt in arg:
            if isinstance(elt,  (GeneratorType, _AlwaysComb, _Always)):
                gens.append(elt)
        return gens


def _inferArgs(arg):
    c = [arg]
    if isinstance(arg, (tuple, list)):
        c += list(arg)
    return c
   


    
    

            
        
    
    
