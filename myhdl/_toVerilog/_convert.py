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

""" myhdl toVerilog conversion module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
import math
import traceback
import inspect
import compiler
from compiler import ast as astNode
from sets import Set
from types import GeneratorType, FunctionType, ClassType
from cStringIO import StringIO
import __builtin__
import warnings

import myhdl
from myhdl import *
from myhdl import ToVerilogError, ToVerilogWarning
from myhdl._extractHierarchy import _HierExtr, _isMem, _getMemInfo, \
     _UserDefinedVerilog, _userDefinedVerilogMap

from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl._toVerilog import _error, _access, _kind,_context, \
     _ToVerilogMixin, _Label
from myhdl._toVerilog._analyze import _analyzeSigs, _analyzeGens, _analyzeTopFunc, \
     _Ram, _Rom
            
_converting = 0
_profileFunc = None

def _checkArgs(arglist):
    for arg in arglist:
        if not type(arg) in (GeneratorType, _AlwaysComb, _Always, _UserDefinedVerilog):
            raise ToVerilogError(_error.ArgType, arg)
        
def _flatten(*args):
    arglist = []
    for arg in args:
        if id(arg) in _userDefinedVerilogMap:
            arglist.append(_userDefinedVerilogMap[id(arg)])
        elif isinstance(arg, (list, tuple, Set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist
        

class _ToVerilogConvertor(object):

    __slots__ = ("name", )

    def __init__(self):
        self.name = None

    def __call__(self, func, *args, **kwargs):
        global _converting
        if _converting:
            return func(*args, **kwargs) # skip
        else:
            # clean start
            sys.setprofile(None)
        from myhdl import _traceSignals
        if _traceSignals._tracing:
            raise ToVerilogError("Cannot use toVerilog while tracing signals")
        if not callable(func):
            raise ToVerilogError(_error.FirstArgType, "got %s" % type(func))

        _converting = 1
        if self.name is None:
            name = func.func_name
        else:
            name = str(self.name)
        try:
            h = _HierExtr(name, func, *args, **kwargs)
        finally:
            _converting = 0

        vpath = name + ".v"
        vfile = open(vpath, 'w')
        tbpath = "tb_" + vpath
        tbfile = open(tbpath, 'w')

        siglist, memlist = _analyzeSigs(h.hierarchy)
        arglist = _flatten(h.top)
        # print h.top
        _checkArgs(arglist)
        genlist = _analyzeGens(arglist, h.absnames)
        intf = _analyzeTopFunc(func, *args, **kwargs)
        intf.name = name

        _writeModuleHeader(vfile, intf)
        _writeSigDecls(vfile, intf, siglist, memlist)
        _convertGens(genlist, vfile)
        _writeModuleFooter(vfile)
        _writeTestBench(tbfile, intf)

        vfile.close()
        tbfile.close()

        # clean up signal names
        for sig in siglist:
            sig._name = None

        return h.top
    

toVerilog = _ToVerilogConvertor()


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
        if s._name is None:
            raise ToVerilogError(_error.ShadowingSignal, portname)
        # make sure signal name is equal to its port name
        s._name = portname
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            print >> f, "output %s%s%s;" % (p, r, portname)
            if s._driven == 'reg':
                print >> f, "reg %s%s%s;" % (p, r, portname)
            else:
                print >> f, "wire %s%s%s;" % (p, r, portname)
        else:
            print >> f, "input %s%s%s;" % (p, r, portname)
    print >> f


def _writeSigDecls(f, intf, siglist, memlist):
    constwires = []
    for s in siglist:
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedSignal, s._name),
                              category=ToVerilogWarning
                              )
            # the following line implements initial value assignments
            # print >> f, "%s %s%s = %s;" % (s._driven, r, s._name, int(s._val))
            print >> f, "%s %s%s%s;" % (s._driven, p, r, s._name)
        elif s._read:
            # the original exception
            # raise ToVerilogError(_error.UndrivenSignal, s._name)
            # changed to a warning and a continuous assignment to a wire
            warnings.warn("%s: %s" % (_error.UndrivenSignal, s._name),
                          category=ToVerilogWarning
                          )
            constwires.append(s)
            print >> f, "wire %s%s;" % (r, s._name)
    print >> f
    for m in memlist:
        if not m.decl:
            continue
        r = _getRangeString(m.elObj)
        print >> f, "reg %s%s [0:%s-1];" % (r, m.name, m.depth)
    print >> f
    for s in constwires:
        print >> f, "assign %s = %s;" % (s._name, int(s._val))
            

def _writeModuleFooter(f):
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
    elif s._nrbits is not None:
        nrbits = s._nrbits
        return "[%s:0] " % (nrbits-1)
    else:
        raise AssertionError

def _getSignString(s):
    if s._min is not None and s._min < 0:
        return "signed "
    else:
        return ''


def _convertGens(genlist, vfile):
    blockBuf = StringIO()
    funcBuf = StringIO()
    for ast in genlist:
        if isinstance(ast, _UserDefinedVerilog):
            blockBuf.write(str(ast))
            continue
        if ast.kind == _kind.ALWAYS:
            Visitor = _ConvertAlwaysVisitor
        elif ast.kind == _kind.INITIAL:
            Visitor = _ConvertInitialVisitor
        elif ast.kind == _kind.SIMPLE_ALWAYS_COMB:
            Visitor = _ConvertSimpleAlwaysCombVisitor
        elif ast.kind == _kind.ALWAYS_DECO:
            Visitor = _ConvertAlwaysDecoVisitor
        else: # ALWAYS_COMB
            Visitor = _ConvertAlwaysCombVisitor
        v = Visitor(ast, blockBuf, funcBuf)
        compiler.walk(ast, v)
    vfile.write(funcBuf.getvalue()); funcBuf.close()
    vfile.write(blockBuf.getvalue()); blockBuf.close()

class _ConvertVisitor(_ToVerilogMixin):
    
    def __init__(self, ast, buf):
        self.ast = ast
        self.buf = buf
        self.returnLabel = ast.name
        self.ind = ''
        self.isSigAss = False
        self.labelStack = []
 
    def write(self, arg):
        self.buf.write("%s" % arg)

    def writeline(self, nr=1):
        for i in range(nr):
            self.buf.write("\n%s" % self.ind)

    def writeIntSize(self, n):
        # write size for large integers (beyond 32 bits signed)
        # with some safety margin
        if n >= 2**30:
            size = int(math.ceil(math.log(n+1,2))) + 1  # sign bit!
            self.write("%s'sd" % size)

    def writeDeclaration(self, obj, name, dir):
        if dir: dir = dir + ' '
        if type(obj) is bool:
            self.write("%s%s" % (dir, name))
        elif isinstance(obj, int):
            if dir == "input ":
                self.write("input %s;" % name)
                self.writeline()
            self.write("integer %s" % name)
        elif isinstance(obj, _Ram):
            self.write("reg [%s-1:0] %s [0:%s-1]" % (obj.elObj._nrbits, name, obj.depth))
        elif hasattr(obj, '_nrbits'):
            s = ""
            if isinstance(obj, (intbv, Signal)):
                if obj._min is not None and obj._min < 0:
                    s = "signed "
            self.write("%s%s[%s-1:0] %s" % (dir, s, obj._nrbits, name))
        else:
            raise AssertionError("var %s has unexpected type %s" % (name, type(obj)))
        # initialize regs
        # if dir == 'reg ' and not isinstance(obj, _Ram):
        # disable for cver
        if False:
            if isinstance(obj, EnumItemType):
                inival = obj._toVerilog()
            else:
                inival = int(obj)
            self.write(" = %s;" % inival)
        else:
            self.write(";")
        

    def writeDeclarations(self):
        for name, obj in self.ast.vardict.items():
            self.writeline()
            self.writeDeclaration(obj, name, "reg")
                
    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def binaryOp(self, node, op=None):
        context = None
        if node.signed:
            context = _context.SIGNED
        self.write("(")
        self.visit(node.left, context)
        self.write(" %s " % op)
        self.visit(node.right, context)
        self.write(")")
    def visitAdd(self, node, *args):
        self.binaryOp(node, '+')
    def visitFloorDiv(self, node, *args):
        self.binaryOp(node, '/')
    def visitLeftShift(self, node, *args):
        self.binaryOp(node, '<<')
    def visitMod(self, node, context=None, *args):
        if context == _context.PRINT:
            self.visit(node.left, _context.PRINT)
            self.write(", ")
            self.visit(node.right, _context.PRINT)
        else:
            self.binaryOp(node, '%')        
    def visitMul(self, node, *args):
        self.binaryOp(node, '*')
    def visitPower(self, node, *args):
         self.binaryOp(node, '**')
    def visitSub(self, node, *args):
        self.binaryOp(node, "-")
    def visitRightShift(self, node, *args):
        # Additional cast to signed of the full expression
        # this is apparently required by cver - not sure if it
        # is actually required by standard Verilog.
        # It shouldn't hurt however.
        if node.signed:
            self.write("$signed")
        self.binaryOp(node, '>>>')

    def checkOpWithNegIntbv(self, node, op):
        if op in ("+", "-", "*", "&&", "||", "!"):
            return
        if isinstance(node, astNode.Name):
            o = node.obj
            if isinstance(o, (Signal, intbv)) and o.min is not None and o.min < 0:
                self.raiseError(node, _error.NotSupported,
                                "negative intbv with operator %s" % op)
        
    def multiOp(self, node, op):
        for n in node.nodes:
            self.checkOpWithNegIntbv(n, op)
        self.write("(")
        self.visit(node.nodes[0])
        for n in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(n)
        self.write(")")
    def visitAnd(self, node, *args):
        self.multiOp(node, '&&')
    def visitBitand(self, node, *args):
        self.multiOp(node, '&')
    def visitBitor(self, node, *args):
        self.multiOp(node, '|')
    def visitBitxor(self, node, *args):
        self.multiOp(node, '^')
    def visitOr(self, node, *args):
        self.multiOp(node, '||')

    def unaryOp(self, node, op, context):
        self.checkOpWithNegIntbv(node.expr, op)
        self.write("(%s" % op)
        self.visit(node.expr, context)
        self.write(")")
    def visitInvert(self, node, context=None, *args):
        self.unaryOp(node, '~', context)
    def visitNot(self, node, context=None, *args):
        self.unaryOp(node, '!', context)
    def visitUnaryAdd(self, node, context=None, *args):
        self.unaryOp(node, '+', context)
    def visitUnarySub(self, node, context=None, *args):
        self.unaryOp(node, '-', context)

    def visitAssAttr(self, node, *args):
        assert node.attrname == 'next'
        self.isSigAss = True
        self.visit(node.expr)

    def visitAssert(self, node, *args):
        # XXX
        pass

    def visitAssign(self, node, *args):
        assert len(node.nodes) == 1
        # shortcut for expansion of ROM in case statement
        if isinstance(node.expr, astNode.Subscript) and \
               isinstance(node.expr.expr.obj, _Rom):
            rom = node.expr.expr.obj.rom
            self.write("// synthesis parallel_case full_case")
            self.writeline()
            self.write("case (")
            self.visit(node.expr.subs[0])
            self.write(")")
            self.indent()
            for i, n in enumerate(rom):
                self.writeline()
                if i == len(rom)-1:
                    self.write("default: ")
                else:
                    self.write("%s: " % i)
                self.visit(node.nodes[0])
                if self.isSigAss:
                    self.write(' <= ')
                    self.isSigAss = False
                else:
                    self.write(' = ')
                self.writeIntSize(n)
                self.write("%s;" % n)
            self.dedent()
            self.writeline()
            self.write("endcase")
            return
        # default behavior
        self.visit(node.nodes[0])
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' = ')
        self.visit(node.expr)
        self.write(';')

    def visitAssName(self, node, *args):
        self.write(node.name)

    def visitAugAssign(self, node, *args):
        opmap = {"+=" : "+",
                 "-=" : "-",
                 "*=" : "*",
                 "//=" : "/",
                 "%=" : "%",
                 "**=" : "**",
                 "|=" : "|",
                 ">>=" : ">>>",
                 "<<=" : "<<",
                 "&=" : "&",
                 "^=" : "^"
                 }
        if node.op not in opmap:
            self.raiseError(node, _error.NotSupported,
                            "augmented assignment %s" % node.op)
        op = opmap[node.op]
        # XXX apparently no signed context required for augmented assigns
        self.visit(node.node)
        self.write(" = ")
        self.visit(node.node)
        self.write(" %s " % op)
        self.visit(node.expr)
        self.write(";")
         
    def visitBreak(self, node, *args):
        self.write("disable %s;" % self.labelStack[-2])

    def visitCallFunc(self, node, *args):
        fn = node.node
        assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        opening, closing = '(', ')'
        if f is bool:
            self.write("(")
            self.visit(node.args[0])
            self.write(" != 0)")
            # self.write(" ? 1'b1 : 1'b0)")
            return
        elif f is len:
            val = self.getVal(node)
            self.require(node, val is not None, "cannot calculate len")
            self.write(`val`)
            return
        elif f in (int, long):
            opening, closing = '', ''
        elif f is intbv:
            self.visit(node.args[0])
            return
        elif type(f) is ClassType and issubclass(f, Exception):
            self.write(f.__name__)
        elif f in (posedge, negedge):
            opening, closing = ' ', ''
            self.write(f.__name__)
        elif f is concat:
            opening, closing = '{', '}'
        elif hasattr(node, 'ast'):
            self.write(node.ast.name)
        else:
            self.write(f.__name__)
        if node.args:
            self.write(opening)
            self.visit(node.args[0])
            for arg in node.args[1:]:
                self.write(", ")
                self.visit(arg)
            self.write(closing)
        if hasattr(node, 'ast'):
            if node.ast.kind == _kind.TASK:
                Visitor = _ConvertTaskVisitor
            else:
                Visitor = _ConvertFunctionVisitor
            v = Visitor(node.ast, self.funcBuf)
            compiler.walk(node.ast, v)

    def visitCompare(self, node, *args):
        context = None
        if node.signed:
            context = _context.SIGNED
        self.write("(")
        self.visit(node.expr, context)
        op, code = node.ops[0]
        self.write(" %s " % op)
        self.visit(code, context)
        self.write(")")

    def visitConst(self, node, context=None, *args):
        if context == _context.PRINT:
            self.write('"%s"' % node.value)
        else:
            self.write(node.value)

    def visitContinue(self, node, *args):
        self.write("disable %s;" % self.labelStack[-1])

    def visitDiscard(self, node, *args):
        expr = node.expr
        self.visit(expr)
        # ugly hack to detect an orphan "task" call
        if isinstance(expr, astNode.CallFunc) and hasattr(expr, 'ast'):
            self.write(';')

    def visitFor(self, node, *args):
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        var = node.assign.name
        cf = node.list
        self.require(node, isinstance(cf, astNode.CallFunc), "Expected (down)range call")
        f = self.getObj(cf.node)
        self.require(node, f in (range, downrange), "Expected (down)range call")
        args = cf.args
        assert len(args) <= 3
        if f is range:
            cmp = '<'
            op = '+'
            oneoff = ''
            if len(args) == 1:
                start, stop, step = None, args[0], None
            elif len(args) == 2:
                start, stop, step = args[0], args[1], None
            else:
                start, stop, step = args
        else: # downrange
            cmp = '>='
            op = '-'
            oneoff ='-1'
            if len(args) == 1:
                start, stop, step = args[0], None, None
            elif len(args) == 2:
                start, stop, step = args[0], args[1], None
            else:
                start, stop, step = args
        if node.breakLabel.isActive:
            self.write("begin: %s" % node.breakLabel)
            self.writeline()
        self.write("for (%s=" % var)
        if start is None:
            self.write("0")
        else:
            self.visit(start)
        self.write("%s; %s%s" % (oneoff, var, cmp))
        if stop is None:
            self.write("0")
        else:
            self.visit(stop)
        self.write("; %s=%s%s" % (var, var, op))
        if step is None:
            self.write("1")
        else:
            self.visit(step)
        self.write(") begin")
        if node.loopLabel.isActive:
            self.write(": %s" % node.loopLabel)
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()

    def visitFunction(self, node, *args):
        raise AssertionError("To be implemented in subclass")

    def visitGetattr(self, node, *args):
        assert isinstance(node.expr, astNode.Name)
        assert node.expr.name in self.ast.symdict
        obj = self.ast.symdict[node.expr.name]
        if isinstance(obj, Signal):
            if node.attrname == 'next':
                self.isSigAss = True
            elif node.attrname in ('posedge', 'negedge'):
                self.write(node.attrname)
                self.write(' ')
            self.visit(node.expr)
        elif isinstance(obj, EnumType):
            assert hasattr(obj, node.attrname)
            e = getattr(obj, node.attrname)
            self.write(e._toVerilog())

    def visitIf(self, node, *args):
        if node.ignore:
            return
        if node.isCase:
            self.mapToCase(node, *args)
        else:
            self.mapToIf(node, *args)

    def mapToCase(self, node, *args):
        var = node.caseVar
        self.write("// synthesis parallel_case")
        if node.isFullCase:
            self.write(" full_case")
        self.writeline()
        self.write("casez (")
        self.visit(var)
        self.write(")")
        self.indent()
        for test, suite in node.tests:
            self.writeline()
            item = test.ops[0][1].obj
            self.write(item._toVerilog(dontcare=True))
            self.write(": begin")
            self.indent()
            self.visit(suite)
            self.dedent()
            self.writeline()
            self.write("end")
        if node.else_:
            self.writeline()
            self.write("default: begin")
            self.indent()
            self.visit(node.else_)
            self.dedent()
            self.writeline()
            self.write("end")
        self.dedent()
        self.writeline()
        self.write("endcase")
        
    def mapToIf(self, node, *args):
        first = True
        for test, suite in node.tests:
            if first:
                ifstring = "if ("
                first = False
            else:
                ifstring = "else if ("
                self.writeline()
            self.write(ifstring)
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

    def visitKeyword(self, node, *args):
        self.visit(node.expr)

    def visitModule(self, node, *args):
        for stmt in node.node.nodes:
            self.visit(stmt)
       
    def visitName(self, node, context=None, *args):
        addSignBit = False
        isMixedExpr = (not node.signed) and (context == _context.SIGNED)
        n = node.name
        if n == 'False':
            s = "0"
        elif n == 'True':
            s = "1"
        elif n in self.ast.vardict:
            addSignBit = isMixedExpr
            s = n
        elif n in self.ast.argnames:
            assert n in self.ast.symdict
            addSignBit = isMixedExpr
            s = n
        elif n in self.ast.symdict:
            obj = self.ast.symdict[n]
            if isinstance(obj, bool):
                s = "%s" % int(obj)
            elif isinstance(obj, (int, long)):
                self.writeIntSize(obj)
                s = str(obj)
            elif isinstance(obj, Signal):
                addSignBit = isMixedExpr
                s = str(obj)
            elif _isMem(obj):
                m = _getMemInfo(obj)
                assert m.name
                if not m.decl:
                    self.raiseError(node, _error.ListElementNotUnique, m.name)
                s = m.name
            elif isinstance(obj, EnumItemType):
                s = obj._toVerilog()
            elif type(obj) is ClassType and issubclass(obj, Exception):
                s = n
            else:
                self.raiseError(node, _error.UnsupportedType, "%s, %s" % (n, type(obj)))
        else:
            raise AssertionError("name ref: %s" % n)
        if addSignBit:
            self.write("$signed({1'b0, ")
        self.write(s)
        if addSignBit:
            self.write("})")       

    def visitPass(self, node, *args):
        self.write("// pass")

    def handlePrint(self, node):
        self.write('$display(')
        s = node.nodes[0]
        self.visit(s, _context.PRINT)
        for s in node.nodes[1:]:
            self.write(', , ')
            self.visit(s, _context.PRINT)
        self.write(');')
    
    def visitPrint(self, node, *args):
        self.handlePrint(node)

    def visitPrintnl(self, node, *args):
        self.handlePrint(node)
    
    def visitRaise(self, node, *args):
        self.write('$display("')
        self.visit(node.expr1)
        self.write('");')
        self.writeline()
        self.write("$finish;")
        
    def visitReturn(self, node, *args):
        self.write("disable %s;" % self.returnLabel)

    def visitSlice(self, node, context=None, *args):
        if isinstance(node.expr, astNode.CallFunc) and \
           node.expr.node.obj is intbv:
            c = self.getVal(node)
            self.write("%s'h" % c._nrbits)
            self.write("%x" % c._val)
            return
        addSignBit = (node.flags == 'OP_APPLY') and (context == _context.SIGNED)
        if addSignBit:
            self.write("$signed({1'b0, ")
        self.visit(node.expr)
        # special shortcut case for [:] slice
        if node.lower is None and node.upper is None:
            return
        self.write("[")
        if node.lower is None:
            self.write("%s" % node.obj._nrbits)
        else:
            self.visit(node.lower)
        self.write("-1:")
        if node.upper is None:
            self.write("0")
        else:
            self.visit(node.upper)
        self.write("]")
        if addSignBit:
            self.write("})")

    def visitStmt(self, node, *args):
        for stmt in node.nodes:
            self.writeline()
            self.visit(stmt)
            # ugly hack to detect an orphan "task" call
            if isinstance(stmt, astNode.CallFunc) and hasattr(stmt, 'ast'):
                self.write(';')

    def visitSubscript(self, node, context=None, *args):
        addSignBit = (node.flags == 'OP_APPLY') and (context == _context.SIGNED)
        if addSignBit:
            self.write("$signed({1'b0, ")
        self.visit(node.expr)
        self.write("[")
        assert len(node.subs) == 1
        self.visit(node.subs[0])
        self.write("]")
        if addSignBit:
            self.write("})")

    def visitTuple(self, node, context=None, *args):
        assert context != None
        if context == _context.PRINT:
            sep = ", "
        else:
            sep = " or "
        tpl = node.nodes
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(sep)
            self.visit(elt)

    def visitWhile(self, node, *args):
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        if node.breakLabel.isActive:
            self.write("begin: %s" % node.breakLabel)
            self.writeline()
        self.write("while (")
        self.visit(node.test)
        self.write(") begin")
        if node.loopLabel.isActive:
            self.write(": %s" % node.loopLabel)
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()
        
    def visitYield(self, node, *args):
        self.write("@ (")
        self.visit(node.value, _context.YIELD)
        self.write(");")

        
class _ConvertAlwaysVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        w = node.code.nodes[-1]
        assert isinstance(w.body.nodes[0], astNode.Yield)
        sl = w.body.nodes[0].value
        self.write("always @(")
        self.visit(sl, _context.YIELD)
        self.write(") begin: %s" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        assert isinstance(w.body, astNode.Stmt)
        for stmt in w.body.nodes[1:]:
            self.writeline()
            self.visit(stmt)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)
        
    
class _ConvertInitialVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("initial begin: %s" % self.ast.name) 
        self.indent()
        self.writeDeclarations()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)


class _ConvertAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("always @(")
        assert self.ast.senslist
        for s in self.ast.senslist[:-1]:
            self.write(s._name)
            self.write(', ')
        self.write(self.ast.senslist[-1]._name)
        self.write(") begin: %s" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)

        
class _ConvertSimpleAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitAssAttr(self, node, *args):
        self.write("assign ")
        self.visit(node.expr)

    def visitFunction(self, node, *args):
        self.visit(node.code)
        self.writeline(2)


        
class _ConvertAlwaysDecoVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("always @(")
        assert self.ast.senslist
        for e in self.ast.senslist[:-1]:
            self.write(e._toVerilog())
            self.write(' or ')
        self.write(self.ast.senslist[-1]._toVerilog())
        self.write(") begin: %s" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)
       
    
class _ConvertFunctionVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnObj = ast.returnObj
        self.returnLabel = _Label("RETURN")

    def writeOutputDeclaration(self):
        obj = self.ast.returnObj
        self.writeDeclaration(obj, self.ast.name, dir='')

    def writeInputDeclarations(self):
        for name in self.ast.argnames:
            obj = self.ast.symdict[name]
            self.writeline()
            self.writeDeclaration(obj, name, "input")
            
    def visitFunction(self, node, *args):
        self.write("function ")
        self.writeOutputDeclaration()
        self.indent()
        self.writeInputDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endfunction")
        self.writeline(2)

    def visitReturn(self, node, *args):
        self.write("%s = " % self.ast.name)
        self.visit(node.value)
        self.write(";")
        self.writeline()
        self.write("disable %s;" % self.returnLabel)
    
    
class _ConvertTaskVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnLabel = _Label("RETURN")

    def writeInterfaceDeclarations(self):
        for name in self.ast.argnames:
            obj = self.ast.symdict[name]
            output = name in self.ast.outputs
            input = name in self.ast.inputs
            inout = input and output
            dir = (inout and "inout") or (output and "output") or "input"
            self.writeline()
            self.writeDeclaration(obj, name, dir)
            
    def visitFunction(self, node, *args):
        self.write("task %s;" % self.ast.name)
        self.indent()
        self.writeInterfaceDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endtask")
        self.writeline(2)
