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

from inspect import currentframe, getouterframes
import inspect
import compiler
from compiler import ast
from sets import Set
from types import GeneratorType
from cStringIO import StringIO

from myhdl import Signal, intbv
from myhdl._extractHierarchy import _HierExtr, _findInstanceName


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
    
class MultipleTracesError(Error):
    """Cannot trace multiple instances simultaneously"""

class UndefinedBitWidthError(Error):
    """Signal has undefined bit width"""

class UndrivenSignalError(Error):
    """Signal is not driven"""


def toVerilog(func, *args, **kwargs):
    global _converting
    if _converting:
        return func(*args, **kwargs) # skip
    if not callable(func):
        raise ArgTypeError("got %s" % type(func))
    _converting = 1
    try:
        outer = getouterframes(currentframe())[1]
        name = _findInstanceName(outer)
        if name is None:
            raise TopLevelNameError
        h = _HierExtr(name, func, *args, **kwargs)
    finally:
        _converting = 0
    vpath = name + ".v"
    vfile = open(vpath, 'w')
    tbpath = "tb_" + vpath
    tbfile = open(tbpath, 'w')
    
    siglist = _analyzeSigs(h.hierarchy)
    astlist = _analyzeGens(_flatten(h.top))
    intf = _analyzeTopFunc(func, *args, **kwargs)
    intf.name = name
    
    _writeModuleHeader(vfile, intf)
    _writeSigDecls(vfile, intf, siglist)
    _convertGens(astlist, vfile)
    _writeModuleFooter(vfile)
    _writeTestBench(tbfile, intf)

    vfile.close()
    tbfile.close()
    
    return h.top



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
        symdict = f.f_globals.copy()
        symdict.update(f.f_locals)
        sigdict = {}
        for n, v in symdict.items():
            if isinstance(v, Signal):
                sigdict[n] = v
        ast.sigdict = sigdict
        ast.symdict = symdict
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
            self.toplevel = 0
            print node.code
            self.visit(node.code)
            isAlways = True
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
        argnames = node.argnames
        for i, arg in enumerate(self.args):
            if isinstance(arg, Signal):
                n = argnames[i]
                self.argdict[n] = arg
        for n in argnames[i+1:]:
            if n in self.kwargs:
                arg = self.kwargs[n]
                if isinstance(arg, Signal):
                    self.argdict[n] = arg
        self.argnames = [n for n in argnames if n in self.argdict]


### Verilog output functions ###

def _writeModuleHeader(f, intf):
    print >> f, "module %s (" % intf.name
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
            

def _writeModuleFooter(f):
    print >> f
    print >> f
    print >> f, "endmodule"
    

def _writeTestBench(f, intf):
    print >> f, "module tb_%s;" % intf.name
    print >> f
    fr = StringIO()
    to = StringIO()
    pm = StringIO()
    for portname in intf.argnames:
        s = intf.argdict[portname]
        r = _getRangeString(s)
        if s._driven:
            print >> f, "wire %s%s;" % (r, portname)
            print >> to, "        %s," % portname
        else:
            print >> f, "reg %s%s;" % (r, portname)
            print >> fr, "        %s," % portname
        print >> pm, "    %s," % portname
    print >> f
    print >> f, "initial begin"
    if fr.getvalue():
        print >> f, "    $from_myhdl("
        print >> f, fr.getvalue()[:-2]
        print >> f, "    );"
    if to.getvalue():
        print >> f, "    $to_myhdl("
        print >> f, to.getvalue()[:-2]
        print >> f, "    );" 
    print >> f, "end"
    print >> f
    print >> f, "%s dut(" % intf.name
    print >> f, pm.getvalue()[:-2]
    print >> f, ");"
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
    
    def __init__(self, f, sigdict, symdict):
        self.buf = self.fileBuf = f
        self.declBuf = StringIO()
        self.codeBuf = StringIO()
        self.sigdict = sigdict
        self.symdict = symdict
        self.ind = ''
        self.inYield = False
        self.isSigAss = False
        self.genLabel = self.LabelGenerator()

    def LabelGenerator(self):
        i = 1
        while 1:
            yield "LABEL_%s" % i
            i += 1

    def write(self, arg):
        self.buf.write("%s" % arg)

    def writeline(self):
        self.buf.write("\n%s" % self.ind)

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

    def visitBitxor(self, node):
        self.write("(")
        self.visit(node.nodes[0])
        for node in node.nodes[1:]:
            self.write(" ^ ")
            self.visit(node)
        self.write(")")


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

    def visitFor(self, node):
        print node.lineno
        assert isinstance(node.assign, ast.AssName)
        var = node.assign.name
        print var
        self.buf = self.declBuf
        self.write("integer %s;" % var)
        self.writeline
        self.buf = self.codeBuf
        cf = node.list
        assert isinstance(cf, ast.CallFunc)
        assert isinstance(cf.node, ast.Name)
        assert cf.node.name == 'range'
        assert len(cf.args) == 1
        d = {'var' : var}
        self.writeline()
        self.write("for (%(var)s=0; %(var)s<" % d)
        self.visit(cf.args[0])
        self.write("; %(var)s=%(var)s+1) begin" % d)
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        assert node.else_ is None
         

    def visitFunction(self, node):
        w = node.code.nodes[-1]
        assert isinstance(w, ast.While)
        assert isinstance(w.test, ast.Const)
        assert w.test.value in ('1', True)
        assert w.else_ is None
        assert isinstance(w.body.nodes[0], ast.Yield)
        sl = w.body.nodes[0].value
        assert isinstance(sl, (ast.Tuple, ast.Name))
        self.inYield = True
        self.write("always @(")
        self.visit(sl)
        self.inYield = False
        self.write(") begin: %s" % self.genLabel.next())
        self.indent()
        self.buf = self.codeBuf
        for s in w.body.nodes[1:]:
            self.visit(s)
        self.buf = self.fileBuf
        self.writeline()
        self.write(self.declBuf.getvalue())
        self.write(self.codeBuf.getvalue())
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()

    def visitGetattr(self, node):
        if node.attrname == 'next':
            self.isSigAss = True
        self.visit(node.expr)
        
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
        if node.name in self.symdict:
            obj = self.symdict[node.name]
            if isinstance(obj, int):
                self.write(str(obj))
            elif type(obj) is Signal:
                self.write(obj._name)
            else:
                self.write(node.name)
        else:
            self.write(node.name)

    def visitSubscript(self, node):
        self.visit(node.expr)
        self.write("[")
        assert len(node.subs) == 1
        self.visit(node.subs[0])
        self.write("]")

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
           v = _convertGenVisitor(vfile, ast.sigdict, ast.symdict)
           compiler.walk(ast, v)
 

    
        
        
