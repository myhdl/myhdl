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

import inspect
import compiler
from compiler import ast
from sets import Set
from types import GeneratorType, ClassType
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
        if self.__doc__ and self.arg:
            msg = self.__doc__ + ": " + str(self.arg)
        else:
            msg = self.__doc__ or self.arg
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
        outer = inspect.getouterframes(inspect.currentframe())[1]
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
    genlist = _analyzeGens(_flatten(h.top), h.gennames)
    intf = _analyzeTopFunc(func, *args, **kwargs)
    intf.name = name
    
    _writeModuleHeader(vfile, intf)
    _writeSigDecls(vfile, intf, siglist)
    _convertGens(genlist, vfile)
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


def LabelGenerator():
    i = 1
    while 1:
        yield "_MYHDL_LABEL_%s" % i
        i += 1
        

def _analyzeGens(top, gennames):
    genLabel = LabelGenerator()
    genlist = []
    for g in top:
        f = g.gi_frame
        s = inspect.getsource(f)
        s = s.lstrip()
        gen = compiler.parse(s)
        gen.sourcefile = inspect.getsourcefile(f)
        gen.lineoffset = inspect.getsourcelines(f)[1]-1
        symdict = f.f_globals.copy()
        symdict.update(f.f_locals)
        sigdict = {}
        for n, v in symdict.items():
            if isinstance(v, Signal):
                sigdict[n] = v
        gen.sigdict = sigdict
        gen.symdict = symdict
        if gennames.has_key(id(g)):
            gen.name = gennames[id(g)]
        else:
            gen.name = genLabel.next()
        v = _AnalyzeGenVisitor(sigdict, gen.sourcefile, gen.lineoffset)
        compiler.walk(gen, v)
        genlist.append(gen)
    return genlist



class ToVerilogError(Error):
    pass
   

class _ToVerilogBaseVisitor(object):
    
    def raiseError(self, msg, node):
        lineno = node.lineno
        if lineno is None:
            for n in node.getChildNodes():
                if n.lineno is not None:
                    lineno = n.lineno
                    break
        lineno = lineno or 0
        msg = "in file %s, line %s:\n    %s" % \
              (self.sourcefile, self.lineoffset+lineno, msg)
        raise ToVerilogError(msg)

    def visitAssList(self, node, *args):
        self.raiseError("list assignment not supported", node)

    def visitAssTuple(self, node, *args):
        self.raiseError("tuple assignment not supported", node)

    def visitBackquote(self, node, *args):
        self.raiseError("backquote not supported", node)

    def visitBreak(self, node, *args):
        self.raiseError("break statement not supported", node)

    def visitClass(self, node, *args):
        self.raiseError("class statement not supported", node)

    def visitContinue(self, node, *args):
        self.raiseError("continue statement not supported", node)

    def visitDict(self, node, *args):
        self.raiseError("dictionaries not supported", node)

    def visitDiv(self, node, *args):
        self.raiseError("true division not supported - consider '//'", node)

    def visitEllipsis(self, node, *args):
        self.raiseError("ellipsis not supported", node)

    def visitExec(self, node, *args):
        self.raiseError("exec not supported", node)

    def visitExpression(self, node, *args):
        self.raiseError("Expression node not supported", node)

    def visitFrom(self, node, *args):
        self.raiseError("from statement not supported", node)
        
    def visitGlobal(self, node, *args):
        self.raiseError("global statement not supported", node)

    def visitImport(self, node, *args):
        self.raiseError("import statement not supported", node)

    def visitLambda(self, node, *args):
        self.raiseError("lambda statement not supported", node)

    def visitListComp(self, node, *args):
        self.raiseError("list comprehensions not supported", node)
        
    def visitList(self, node, *args):
        self.raiseError("lists not supported", node)
        
    def visitPower(self, node, *args):
        self.raiseError("power operator not supported", node)

    def visitReturn(self, node, *args):
        self.raiseError("return statement not supported", node)

    def visitTryExcept(self, node, *args):
        self.raiseError("try-except statement not supported", node)
        
    def visitTryFinally(self, node, *args):
        self.raiseError("try-finally statement not supported", node)

    def visitUnaryAdd(self, node, *args):
        self.raiseError("unary add not suported", node)
        
    def visitUnarySub(self, node, *args):
        self.raiseError("unary sub not suported", node)


class SignalAsInoutError(Error):
    """signal used as inout"""
    
class SignalMultipleDrivenError(Error):
    """signal has multiple drivers"""

  
INPUT, OUTPUT, INOUT = range(3)

class _AnalyzeGenVisitor(_ToVerilogBaseVisitor):
    
    def __init__(self, sigdict, sourcefile, lineoffset):
        self.sourcefile = sourcefile
        self.lineoffset = lineoffset
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
        print node.expr
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
        
                
def _analyzeTopFunc(func, *args, **kwargs):
    s = inspect.getsource(func)
    s = s.lstrip()
    funcast = compiler.parse(s)
    v = _AnalyzeTopFuncVisitor(*args, **kwargs)
    compiler.walk(funcast, v)
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
        i=-1
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
    elif s._nrbits is not None:
        return "[%s:0] " % (s._nrbits-1)
    else:
        raise AssertionError
    

    
class _ConvertGenVisitor(object):
    
    def __init__(self, f, sigdict, symdict, name, sourcefile, lineoffset):
        self.buf = self.fileBuf = f
        self.name = name
        self.sourcefile = sourcefile
        self.lineoffset = lineoffset
        self.declBuf = StringIO()
        self.codeBuf = StringIO()
        self.sigdict = sigdict
        self.symdict = symdict
        self.ind = ''
        self.inYield = False
        self.isSigAss = False
        self.toplevel = 1

    def raiseError(self, msg, node):
        lineno = node.lineno
        if lineno is None:
            for n in node.getChildNodes():
                if n.lineno is not None:
                    lineno = n.lineno
                    break
        lineno = lineno or 0
        msg = "in file %s, line %s:\n    %s" % \
              (self.sourcefile, self.lineoffset+lineno, msg)
        raise ToVerilogError(msg)

    def write(self, arg):
        self.buf.write("%s" % arg)

    def writeline(self):
        self.buf.write("\n%s" % self.ind)

    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def binaryOp(self, node, op):
        self.write("(")
        self.visit(node.left)
        self.write(" %s " % op)
        self.visit(node.right)
        self.write(")")

    def multiOp(self, node, op):
        self.write("(")
        self.visit(node.nodes[0])
        for node in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(node)
        self.write(")")
        
    def visitAdd(self, node):
        self.binaryOp(node, '+')
        
    def visitAnd(self, node):
        self.multiOp(node, '&&')

    def visitAssAttr(self, node):
        # if not node.a
        # assert node.attrname == 'next'
        if node.attrname != 'next':
            self.raiseError("attribute assignment not supported", node)
        self.isSigAss = True
        self.visit(node.expr)

    def visitAssert(self, node):
        # XXX
        pass

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

    def visitAssName(self, node):
        # XXX
        pass

    def visitAugAssign(self, node):
        # XXX
        pass

    def visitBitand(self, node):
        self.multiOp(node, '&')
        
    def visitBitor(self, node):
        self.multiOp(node, '|')
         
    def visitBitxor(self, node):
        self.multiOp(node, '^')

    def visitCallFunc(self, node):
        f = node.node
        assert isinstance(f, ast.Name)
        if f.name == 'bool':
            self.write("(")
            self.visit(node.args[0])
            self.write(" ? 1'b1 : 1'b0)")
        else:
            self.visit(f)
            if f.name in self.symdict:
                obj = self.symdict[f.name]
            elif f.name in __builtins__:
                obj = __builtins__[f.name]
            else:
                raise AssertionError
            if type(obj) in (ClassType, type) and issubclass(obj, Exception):
                self.write(": ")
            else:
                self.write(' ')
            if node.args:
                self.visit(node.args[0])
                # XXX

    def visitCompare(self, node):
        self.write("(")
        self.visit(node.expr)
        assert len(node.ops) == 1
        op, code = node.ops[0]
        self.write(" %s " % op)
        self.visit(code)
        self.write(")")

    def visitConst(self, node):
        self.write(node.value)

    def visitFloorDiv(self, node):
        self.binaryOp(node, '/')

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
        if not self.toplevel:
            self.raiseError("embedded function definition not supported", node)
        self.toplevel = 0
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
        self.write(") begin: %s" % self.name)
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
        assert isinstance(node.expr, ast.Name)
        assert node.expr.name in self.symdict
        obj = self.symdict[node.expr.name]
        if type(obj) is Signal:
            if node.attrname == 'next':
                self.isSigAss = True
            self.visit(node.expr)
        elif str(type(obj)) == "<class 'myhdl._enum.Enum'>":
            assert hasattr(obj, node.attrname)
            e = getattr(obj, node.attrname)
            self.write("%d'b%s" % (obj._nrbits, e._val))
        
    def visitIf(self, node):
        ifstring = "if ("
        for test, suite in node.tests:
            self.writeline()
            self.write(ifstring)
            self.visit(test)
            self.write(") begin")
            self.indent()
            self.visit(suite)
            self.dedent()
            self.writeline()
            self.write("end")
            ifstring = "else if ("
        if node.else_:
            self.writeline()
            self.write("else begin")
            self.indent()
            self.visit(node.else_)
            self.dedent()
            self.writeline()
            self.write("end")

    def visitInvert(self, node):
        self.write("(~")
        self.visit(node.expr)
        self.write(")")

    def visitKeyword(self, node):
        # XXX
        pass

    def visitLeftShift(self, node):
        self.binaryOp(node, '<<')

    def visitMod(self, node):
        self.write("(")
        self.visit(node.left)
        self.write(" % ")
        self.visit(node.right)
        self.write(")")
        
    def visitMul(self, node):
        self.binaryOp(node, '*')
       
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

    def visitNot(self, node):
        self.write("(!")
        self.visit(node.expr)
        self.write(")")
        
    def visitOr(self, node):
        self.multiOp(node, '||')

    def visitPass(self, node):
        # XXX
        pass
    
    def visitPrint(self, node):
        # XXX
        pass

    def visitPrintnl(self, node):
        # XXX
        pass
    
    def visitRaise(self, node):
        self.writeline()
        self.write('$display("')
        self.visit(node.expr1)
        self.write('");')
        self.writeline()
        self.write("$finish;")

    def visitRightShift(self, node):
        self.binaryOp(node, '>>')

    def visitSlice(self, node):
        # XXX
        pass

    def visitSliceObj(self, node):
        # XXX
        pass
            
    def visitSub(self, node):
        self.binaryOp(node, "-")

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

    def visitWhile(self, node):
        # XXX
        pass
        
    def visitYield(self, node):
        self.inYield = True
        self.writeline()
        self.write("@ (")
        self.visit(node.value)
        self.write(");")
        self.inYield = False

        

def _convertGens(genlist, vfile):
    for gen in genlist:
        print gen.sourcefile
        print gen.lineoffset
        v = _ConvertGenVisitor(vfile, gen.sigdict, gen.symdict, gen.name,
                               gen.sourcefile, gen.lineoffset )
        compiler.walk(gen, v)
 

    
        
        
