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

""" myhdl toVerilog module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
from inspect import currentframe, getsource, getouterframes
import inspect
import re
import string
import time
from types import FunctionType
import os
from os import path
import shutil
import compiler
from compiler import ast
import linecache
from sets import Set
from types import GeneratorType
from cStringIO import StringIO

from myhdl import _simulator, Signal, __version__, intbv
from myhdl._util import _isGenSeq, _isgeneratorfunction


def _flatten(*args):
    l = []
    for arg in args:
        if type(arg) is GeneratorType:
            l.append(arg)
        elif isinstance(arg, (list, tuple)):
            l.extend(flatten(arg))
        else:
            raise ArgumentError
    return l


_converting = 0
_profileFunc = None

class Error(Exception):
    """ toVerilog Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class TopLevelNameError(Error):
    """result of toVerilog call should be assigned to a top level name"""

class ArgTypeError(Error):
    """toVerilog first argument should be a classic function"""
    
class NoInstancesError(Error):
    """toVerilog returned no instances"""

class MultipleTracesError(Error):
    """Cannot trace multiple instances simultaneously"""

class UndefinedBitWidthError(Error):
    """Signal has undefined bit width"""

class UndrivenSignalError(Error):
    """Signal is not driven"""

re_assign = r"""^
                \s*
                (?P<name>\w[\w\d]*)
                (?P<index>\[.*\])?
                \s*
                =
                """
 
rex_assign = re.compile(re_assign, re.X)


def toVerilog(func, *args, **kwargs):
    global _converting
    if _converting:
        return func(*args, **kwargs) # skip
    if not callable(func):
        raise ArgTypeError("got %s" % type(func))
    if _isgeneratorfunction(func):
        raise ArgTypeError("got generator function")
    _converting = 1
    try:
        outer = getouterframes(currentframe())[1]
        name = _findInstanceName(outer)
        if name is None:
            raise TopLevelNameError
        h = _HierExtr(name, func, *args, **kwargs)
    finally:
        _converting = 0
        linecache.clearcache()
    vpath = name + ".v"
    vfile = open(vpath, 'w')
    
    siglist = _analyzeSigs(h.hierarchy)

    astlist = _analyzeGens(_flatten(h.top))

    intf = _analyzeTopFunc(func, *args, **kwargs)
    
    _writeVerilogHeader(vfile, intf)
    _writeSigDecls(vfile, intf, siglist)
    _convertGens(astlist, vfile)
    _writeVerilogFooter(vfile)
    
    return h.top


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
    
    def __init__(self, name, func, *args, **kwargs):
        global _profileFunc
        self.skipNames = ('always_comb', 'instances', 'processes')
        self.skip = 0
        self.names = [name]
        self.hierarchy = hierarchy = []
        self.level = 0
        _profileFunc = self.extractor
        sys.setprofile(_profileFunc)
        try:
            _top = func(*args, **kwargs)
        finally:
            sys.setprofile(None)
        if not hierarchy:
            raise NoInstancesError
        self.top = _top
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
                        for dict in (frame.f_locals, frame.f_globals):
                            for n, v in dict.items():
                                if isinstance(v, Signal) and n not in sigdict:
                                    sigdict[n] = v
                        i = [self.level, name, sigdict]
                        self.hierarchy.append(i)
                    self.level -= 1
            func_name = frame.f_code.co_name
            if func_name in self.skipNames:
                self.skip = 0
          

   

def _analyzeSigs(hierarchy):
    curlevel = 0
    siglist = []
    prefixes = []
    for level, name, sigdict in hierarchy:
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta == -1:
            prefixes.append(name)
        elif delta == 0:
            prefixes.pop()
            prefixes.append(name)
        else:
            prefixes = prefixes[:curlevel]
        for n, s in sigdict.items():
            if s._name is None:
                if len(prefixes) > 1:
                    s._name = '_'.join(prefixes) + '_' + n
                else:
                    s._name = n
                siglist.append(s)
            if not s._nrbits:
                raise UndefinedBitWidthError(s._name)
    return siglist


def _analyzeGens(top):
    genlist = []
    for g in top:
        f = g.gi_frame
        s = inspect.getsource(f)
        s = s.lstrip()
        ast = compiler.parse(s)
        ast.locals = f.f_locals
        ast.globals = f.f_globals
        sigdict = {}
        for dict in (f.f_locals, f.f_globals):
            for n, v in dict.items():
                if isinstance(v, Signal) and n not in sigdict:
                    sigdict[n] = v
        ast.sigdict = sigdict
        v = _AnalyzeGenVisitor(sigdict)
        compiler.walk(ast, v)
        genlist.append(ast)
    return genlist


class SignalAsInoutError(Error):
    """signal used as inout"""
    
class SignalMultipleDrivenError(Error):
    """signal has multiple drivers"""

class EmbeddedFunctionError(Error):
    """embedded functions not supported"""
   
        
INPUT, OUTPUT, INOUT = range(3)

class _AnalyzeGenVisitor(object):
    
    def __init__(self, sigdict):
        self.inputs = Set()
        self.outputs = Set()
        self.toplevel = 1
        self.sigdict = sigdict

    def visitModule(self, node):
        self.visit(node.node)
        for n in self.outputs:
            s = self.sigdict[n]
            if s._driven:
                raise SignalMultipleDrivenError(n)
            s._driven = True
        for n in self.inputs:
            s = self.sigdict[n]
            s._read = True
           
    def visitFunction(self, node):
        if self.toplevel:
            self.toplevel = 0 # skip embedded functions
            print node.code
            self.visit(node.code)
        else:
            raise EmbeddedFunctionError

    def visitName(self, node, access=INPUT):
        n = node.name
        if n not in self.sigdict:
            return
        if access == INPUT:
            self.inputs.add(n)
        elif access == OUTPUT:
            self.outputs.add(n)
        else: 
            raise AssertionError
            
    def visitAssign(self, node, access=OUTPUT):
        for n in node.nodes:
            self.visit(n, OUTPUT)
        self.visit(node.expr, INPUT)

    def visitAssAttr(self, node, access=OUTPUT):
        self.visit(node.expr, OUTPUT)

    def visitSubscript(self, node, access=INPUT):
        self.visit(node.expr, access)
        for n in node.subs:
            self.visit(n, INPUT)

    def visitSlice(self, node, access=INPUT):
        self.visit(node.expr, access)
        if node.lower:
            self.visit(node.lower, INPUT)
        if node.upper:
            self.visit(node.upper, INPUT)

    def visitAugAssign(self, node, access=INPUT):
        self.visit(node.node, INOUT)
        self.visit(node.expr, INPUT)
        
    def visitClass(self, node):
        pass # skip

    def visitExec(self, node):
        pass # skip
           
                
def _analyzeTopFunc(func, *args, **kwargs):
    s = inspect.getsource(func)
    s = s.lstrip()
    ast = compiler.parse(s)
    v = _AnalyzeTopFuncVisitor(*args, **kwargs)
    compiler.walk(ast, v)
    return v
      
    
#Masks for co_flags
#define CO_OPTIMIZED	0x0001
#define CO_NEWLOCALS	0x0002
#define CO_VARARGS	0x0004
#define CO_VARKEYWORDS	0x0008
#define CO_NESTED       0x0010
#define CO_GENERATOR    0x0020
    
class _AnalyzeTopFuncVisitor(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.name = None
        self.argdict = {}
    
    def visitFunction(self, node):
        if node.flags != 0: # check flags
            raise AssertionError("unsupported function type")
        self.name = node.name
        self.argnames = node.argnames
        for argname, arg in zip(node.argnames, self.args):
            self.argdict[argname] = arg
        self.argdict.update(self.kwargs)           
            
        

def _writeVerilogHeader(f, intf):
    print >> f, "module %s (" %intf.name
    b = StringIO()
    for portname in intf.argnames:
        print >> b, "    %s," % portname
    print >> f, b.getvalue()[:-2]
    b.close()
    print >> f, ");"
    print >> f
    for portname in intf.argnames:
        s = intf.argdict[portname]
        assert (s._name == portname)
        r = _getRangeString(s)
        if s._driven:
            print >> f, "output %s%s;" % (r, portname)
            print >> f, "reg %s%s;" % (r, portname)
        else:
            print >> f, "input %s%s;" % (r, portname)
    print >> f


def _writeSigDecls(f, intf, siglist):
    for s in siglist:
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        if s._driven:
            print >> f, "reg %s%s;" % (r, s._name)
        else:
            raise UndrivenSignalError(s._name)
    print >> f
            

def _writeVerilogFooter(f):
    print >> f
    print >> f
    print >> f, "endmodule"

    
def _getRangeString(s):
    if s._type is bool:
        return ''
    elif s._type is intbv:
        return "[%s:0] " % (s._nrbits-1)
    else:
        raise AssertionError
    

    
    
class _convertGenVisitor(object):
    
    def __init__(self, f, sigdict):
        self.f = f
        self.ind = ''
        self.inYield = False
        self.isSigAss = False

    def write(self, arg):
        self.f.write("%s" % arg)

    def writeline(self):
        self.f.write("\n%s" % self.ind)

    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def visitAdd(self, node):
        self.write("(")
        self.visit(node.left)
        self.write(" + ")
        self.visit(node.right)
        self.write(")")

    def visitAssAttr(self, node):
        assert node.attrname == 'next'
        self.isSigAss = True
        self.visit(node.expr)

    def visitAssign(self, node):
        self.writeline()
        assert len(node.nodes) == 1
        self.visit(node.nodes[0])
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' = ')
        self.visit(node.expr)
        self.write(';')

    def visitCallFunc(self, node):
        self.visit(node.node)
        self.write(' ')
        self.visit(node.args[0])
        

    def visitCompare(self, node):
        self.visit(node.expr)
        assert len(node.ops) == 1
        op, code = node.ops[0]
        self.write(" %s " % op)
        self.visit(code)

    def visitConst(self, node):
        self.write(node.value)


    def visitIf(self, node):
        self.writeline()
        self.write("if (")
        test, suite = node.tests[0]
        self.visit(test)
        self.write(") begin")
        self.indent()
        self.visit(suite)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.else_:
            self.writeline()
            self.write("else begin")
            self.indent()
            self.visit(node.else_)
            self.dedent()
            self.writeline()
            self.write("end")

    def visitMod(self, node):
        self.visit(node.left)
        self.write(" % ")
        self.visit(node.right)
        
    def visitName(self, node):
        self.write(node.name)

    def visitTuple(self, node):
        assert self.inYield
        tpl = node.nodes
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(" or ")
            self.visit(elt)
        
    def visitYield(self, node):
        self.inYield = True
        self.writeline()
        self.write("@ (")
        self.visit(node.value)
        self.write(");")
        self.inYield = False

    

    
        
        

def _convertGens(astlist, vfile):
    for ast in astlist:
           v = _convertGenVisitor(vfile, ast.sigdict)
           compiler.walk(ast, v)
 

    
        
        
