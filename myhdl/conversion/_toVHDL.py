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
__revision__ = "$Revision: 811 $"
__date__ = "$Date: 2006-03-31 22:09:27 +0200 (Fri, 31 Mar 2006) $"

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
from myhdl import ToVHDLError, ToVHDLWarning
from myhdl._extractHierarchy import (_HierExtr, _isMem, _getMemInfo,
                                     _UserDefinedVerilog, _userDefinedVerilogMap)

from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl.conversion._misc import (_error, _access, _kind,_context,
                                    _ConversionMixin, _Label)
from myhdl.conversion._analyze import (_analyzeSigs, _analyzeGens, _analyzeTopFunc,
                                       _Ram, _Rom)
from myhdl._Signal import _WaiterList
            
_converting = 0
_profileFunc = None
_enumTypeList = []

def _checkArgs(arglist):
    for arg in arglist:
        if not type(arg) in (GeneratorType, _AlwaysComb, _Always, _UserDefinedVerilog):
            raise ToVHDLError(_error.ArgType, arg)
        
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
        

class _ToVHDLConvertor(object):

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
            raise ToVHDLError("Cannot use toVerilog while tracing signals")
        if not callable(func):
            raise ToVHDLError(_error.FirstArgType, "got %s" % type(func))

        _converting = 1
        if self.name is None:
            name = func.func_name
        else:
            name = str(self.name)
        try:
            h = _HierExtr(name, func, *args, **kwargs)
        finally:
            _converting = 0

        vpath = name + ".vhd"
        vfile = open(vpath, 'w')

        siglist, memlist = _analyzeSigs(h.hierarchy)
        arglist = _flatten(h.top)
        # print h.top
        _checkArgs(arglist)
        genlist = _analyzeGens(arglist, h.absnames)
        _annotateTypes(genlist)
        intf = _analyzeTopFunc(func, *args, **kwargs)
        intf.name = name

        _writeModuleHeader(vfile, intf)
        _writeFuncDecls(vfile)
        _writeSigDecls(vfile, intf, siglist, memlist)
        _convertGens(genlist, vfile)
        _writeModuleFooter(vfile)

        vfile.close()
        # tbfile.close()

        # clean up signal names
        for sig in siglist:
            sig._name = None
            sig._driven = False
            sig._read = False
        # clean up enum type names
        for enumType in _enumTypeList:
            enumType._clearDeclared()

        return h.top
    

toVHDL = _ToVHDLConvertor()


def _writeModuleHeader(f, intf):
    print >> f, "library IEEE;"
    print >> f, "use IEEE.std_logic_1164.all;"
    print >> f, "use IEEE.numeric_std.all;"
    print >> f, "use std.textio.all;"
    print >> f
    print >> f, "entity %s is" % intf.name
    if intf.argnames:
        f.write("    port (")
        c = ''
        for portname in intf.argnames:
            s = intf.argdict[portname]
            f.write("%s" % c)
            c = ';'
            if s._name is None:
                raise ToVHDLError(_error.ShadowingSignal, portname)
            # make sure signal name is equal to its port name
            s._name = portname
            r = _getRangeString(s)
            p = _getTypeString(s)
            if s._driven:
                f.write("\n        %s: out %s%s" % (portname, p, r))
            else:
                f.write("\n        %s: in %s%s" % (portname, p, r))
        f.write("\n    );\n")
    print >> f, "end entity %s;" % intf.name
    print >> f
    print >> f, "architecture MyHDL of %s is" % intf.name
    print >> f


funcdecls = """\
function to_std_logic (arg : boolean) return std_logic is begin
    if arg then
        return '1';
    else
        return '0';
    end if;
end function to_std_logic;
"""

def _writeFuncDecls(f):
    print >> f, funcdecls


constwires = []


def _writeSigDecls(f, intf, siglist, memlist):
    del constwires[:]
    for s in siglist:
        if s._name in intf.argnames:
            continue
        if isinstance(s._val, EnumItemType):
            _declareEnumType(f, s)
        r = _getRangeString(s)
        p = _getTypeString(s)
        if s._driven:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedSignal, s._name),
                              category=ToVHDLWarning
                              )
            # the following line implements initial value assignments
            # print >> f, "%s %s%s = %s;" % (s._driven, r, s._name, int(s._val))
            print >> f, "signal %s: %s%s;" % (s._name, p, r)
        elif s._read:
            # the original exception
            # raise ToVHDLError(_error.UndrivenSignal, s._name)
            # changed to a warning and a continuous assignment to a wire
            warnings.warn("%s: %s" % (_error.UndrivenSignal, s._name),
                          category=ToVHDLWarning
                          )
            constwires.append(s)
            print >> f, "signal %s: %s%s;" % (s._name, p, r)
    for m in memlist:
        if not m.decl:
            continue
        r = _getRangeString(m.elObj)
        print >> f, "reg %s%s [0:%s-1];" % (r, m.name, m.depth)
    print >> f
            

def _writeModuleFooter(f):
    print >> f, "end architecture MyHDL;"

    
def _declareEnumType(f, s):
    enumType = s._val._type
    if enumType._isDeclared():
        return
    else:
        print >> f, enumType._toVHDL(s._name)
        enumType._setDeclared()
        _enumTypeList.append(enumType)

    
def _getRangeString(s):
    if isinstance(s._val, EnumItemType):
        return ''
    elif s._type is bool:
        return ''
    elif s._nrbits is not None:
        nrbits = s._nrbits
        return "(%s downto 0)" % (nrbits-1)
    else:
        raise AssertionError


def _getTypeString(s):
    if isinstance(s._val, EnumItemType):
        return s._val._type._name
    elif s._type is bool:
        return "std_logic"
    if s._min is not None and s._min < 0:
        return "signed "
    else:
        return 'unsigned'


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
    # print >> vfile
    vfile.write(funcBuf.getvalue()); funcBuf.close()
    print >> vfile, "begin"
    print >> vfile
    for s in constwires:
        if s._type is bool:
            pre, suf = "'", "'"
        elif s._type is intbv:
            w = len(s)
            assert w != 0
            if s._min < 0:
                pre, suf = "to_signed(", ", %s)" % w
            else:
                pre, suf = "to_unsigned(", ", %s)" % w
        else:
            assert 0
        print >> vfile, "%s <= %s%s%s;" % (s._name, pre, int(s._val), suf)
    print >> vfile
    vfile.write(blockBuf.getvalue()); blockBuf.close()

class _ConvertVisitor(_ConversionMixin):
    
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

    def writeDeclaration(self, obj, name, kind="", dir="", endchar=";", constr=True):
        if isinstance(obj, EnumItemType):
            enumType = obj._type
            if not enumType._isDeclared():
                self.write(enumType._toVHDL('XXX'))
                self.writeline()
                enumType._setDeclared()
                _enumTypeList.append(enumType)
            tipe = obj._type._name
        elif isinstance(obj, _Ram):
            tipe = "reg [%s-1:0] %s [0:%s-1]" % (obj.elObj._nrbits, name, obj.depth)
        else:
            vhd = inferVhdlObj(obj)
            tipe = vhd.toStr(constr)
        if kind: kind += " "
        if dir: dir += " "
        self.write("%s%s: %s%s%s" % (kind, name, dir, tipe, endchar))
         

##     def writeDeclaration(self, obj, name, dir, endchar=";"):
##         if dir: dir = dir + ' '
##         if type(obj) is bool:
##             self.write("%s%s: std_logic" % (dir, name))
##         elif isinstance(obj, EnumItemType):
##             self.write("%s%s: %s" % (dir, name, obj._type._name))
##         elif isinstance(obj, int):
##             if dir == "input ":
##                 self.write("input %s;" % name)
##                 self.writeline()
##             self.write("variable %s: integer" % name)
##         elif isinstance(obj, _Ram):
##             self.write("reg [%s-1:0] %s [0:%s-1]" % (obj.elObj._nrbits, name, obj.depth))
##         elif hasattr(obj, '_nrbits'):
##             s = "unsigned"
##             if isinstance(obj, (intbv, Signal)):
##                 if obj._min is not None and obj._min < 0:
##                     s = "signed "
##             if dir == "in ":
##                 self.write("%s: %s %s(%s-1 downto 0)" % (name, dir, s, obj._nrbits))
##             else:
##                 self.write("%s%s: %s(%s-1 downto 0)" % (dir, name, s, obj._nrbits))
##         else:
##             raise AssertionError("var %s has unexpected type %s" % (name, type(obj)))
##         # initialize regs
##         # if dir == 'reg ' and not isinstance(obj, _Ram):
##         # disable for cver
##         if False:
##             if isinstance(obj, EnumItemType):
##                 inival = obj._toVHDL()
##             else:
##                 inival = int(obj)
##             self.write(" = %s;" % inival)
##         else:
##             self.write(endchar)

    def writeDeclarations(self):
        if self.ast.hasPrint:
            self.writeline()
            self.write("variable L: line;")
        for name, obj in self.ast.vardict.items():
            if isinstance(obj, _loopInt):
                continue # hack for loop vars
            self.writeline()
            self.writeDeclaration(obj, name, kind="variable")
                
    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def binaryOp(self, node, op=None):
        pre, suf = "", ""
        prel, sufl = "", ""
        prer, sufr = "", ""
        n, o, l, r = node.vhd, node.vhdOri, node.left.vhd, node.right.vhd
        ns, os, ls, rs = n.size, o.size, l.size, r.size
        ds = ns - os
        if isinstance(o, vhd_int):
            if isinstance(n, vhd_unsigned):
                pre, suf = "to_unsigned(", ", %s)" % node.vhd.size
            elif isinstance(n, vhd_signed):
                pre, suf = "to_signed(", ", %s)" % node.vhd.size
            elif isinstance(n, vhd_int):
                pass
            else:
                self.raiseError(node, "Not implemented")
        elif isinstance(l, vhd_unsigned) and isinstance(r, (vhd_int, vhd_unsigned)):
##             if op == '+':
##                 print ns
##                 print os
##                 print ds
            if ds > 0:
                prel, sufl = "resize(", ", %s)" % ns
            elif ds < 0:
                pre, suf = "resize(", ", %s)" % ns

        context = None
        self.write(pre)
        self.write("(")
        self.write(prel)
        self.visit(node.left, context)
        self.write(sufl)
        self.write(" %s " % op)
        self.write(prer)
        self.visit(node.right, context)
        self.write(sufr)
        self.write(")")
        self.write(suf)
    def visitAdd(self, node, *args):
        self.binaryOp(node, '+')
    def visitFloorDiv(self, node, *args):
        self.binaryOp(node, '/')
    def visitMod(self, node, context=None, *args):
        if context == _context.PRINT:
            self.visit(node.left, _context.PRINT)
            self.write(", ")
            self.visit(node.right, _context.PRINT)
        else:
            self.binaryOp(node, 'mod')        
    def visitMul(self, node, *args):
        self.binaryOp(node, '*')
    def visitPower(self, node, *args):
         self.binaryOp(node, '**')
    def visitSub(self, node, *args):
        self.binaryOp(node, "-")


    def shiftOp(self, node, op=None):
        pre, suf = "", ""
        prel, sufl = "", ""
        prer, sufr = "", ""
        if isinstance(node.vhd, vhd_type):
            ts = node.vhd.size
        if isinstance(node.left.vhd, vhd_int):
            if isinstance(node.vhd, vhd_unsigned):
                pre, suf = "to_unsigned(", ", %s)" % ts
            elif isinstance(node.vhd, vhd_signed):
                pre, suf = "to_signed(", ", %s)" % ts
            else:
                raise NotImplementedError
        elif isinstance(node.left.vhd, vhd_unsigned):
            ns = node.left.vhd.size
            ds = ts - ns
            if isinstance(node.vhd, vhd_unsigned):
                if ds > 0:
                    prel, sufl = "resize(", ", %s)" % ts
                elif ds < 0:
                    pre, suf = "resize(", ", %s)" % ts
            else:
                raise NotImplementedError
        else:
            assert NotImplementedError
        self.write(pre)
        self.write("%s(" % op)
        self.write(prel)
        self.visit(node.left)
        self.write(sufl)
        self.write(", ")
        self.write(prer)
        self.visit(node.right)
        self.write(sufr)
        self.write(")")
        self.write(suf)



        
    def visitLeftShift(self, node, *args):
        self.shiftOp(node, "shift_left")
    def visitRightShift(self, node, *args):
        self.shiftOp(node, "shift_right")

    def checkOpWithNegIntbv(self, node, op):
        if op in ("+", "-", "*", "&&", "||", "!"):
            return
        if isinstance(node, astNode.Name):
            o = node.obj
            if isinstance(o, (Signal, intbv)) and o.min is not None and o.min < 0:
                self.raiseError(node, _error.NotSupported,
                                "negative intbv with operator %s" % op)
        
    def multiBoolOp(self, node, op):
        for n in node.nodes:
            self.checkOpWithNegIntbv(n, op)
        if isinstance(node.vhd, vhd_std_logic):
            self.write("to_std_logic")
        self.write("(")
        self.visit(node.nodes[0])
        for n in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(n)
        self.write(")")
    def visitAnd(self, node, *args):
        self.multiBoolOp(node, 'and')
    def visitOr(self, node, *args):
        self.multiBoolOp(node, 'or')
        
    def multiBitOp(self, node, op):
        for n in node.nodes:
            self.checkOpWithNegIntbv(n, op)
        self.write("(")
        self.visit(node.nodes[0])
        for n in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(n)
        self.write(")")
    def visitBitand(self, node, *args):
        self.multiBitOp(node, 'and')
    def visitBitor(self, node, *args):
        self.multiBitOp(node, 'or')
    def visitBitxor(self, node, *args):
        self.multiBitOp(node, 'xor')

    def unaryOp(self, node, op, context):
        self.checkOpWithNegIntbv(node.expr, op)
        self.write("(%s" % op)
        self.visit(node.expr, context)
        self.write(")")
    def visitInvert(self, node, context=None, *args):
        self.unaryOp(node, 'not ', context)
    def visitUnaryAdd(self, node, context=None, *args):
        self.unaryOp(node, '+', context)
    def visitUnarySub(self, node, context=None, *args):
        self.unaryOp(node, '-', context)
    def visitNot(self, node, context=None):
        self.checkOpWithNegIntbv(node.expr, 'not ')
        if isinstance(node.vhd, vhd_std_logic):
            self.write("to_std_logic")
        self.write("(not ")
        self.visit(node.expr, context)
        self.write(")")

        

    def visitAssAttr(self, node, *args):
        assert node.attrname == 'next'
        self.isSigAss = True
        self.visit(node.expr)
        node.obj = self.getObj(node.expr)
    def visitAssert(self, node, *args):
        # XXX
        pass

    def visitAssign(self, node, *args):
        assert len(node.nodes) == 1
        lhs = node.nodes[0]
        rhs = node.expr
        # shortcut for expansion of ROM in case statement
        if isinstance(node.expr, astNode.Subscript) and \
               isinstance(node.expr.expr.obj, _Rom):
            rom = node.expr.expr.obj.rom
            self.write("case ")
            self.visit(node.expr.subs[0])
            self.write(" is")
            self.indent()
            size = lhs.vhd.size
            for i, n in enumerate(rom):
                self.writeline()
                if i == len(rom)-1:
                    self.write("when others => ")
                else:
                    self.write("when %s => " % i)
                self.visit(lhs)
                if self.isSigAss:
                    self.write(' <= ')
                    self.isSigAss = False
                else:
                    self.write(' := ')
                if isinstance(lhs.vhd, vhd_std_logic):
                    self.write("'%s';" % n)
                elif isinstance(lhs.vhd, vhd_int):
                    self.write("%s;" % n)
                else:
                    self.write('"%s";' % bin(n, size))
            self.dedent()
            self.writeline()
            self.write("end case;")
            return
        # default behavior
        convOpen, convClose = "", ""
##         if isinstance(lhs.vhd, vhd_unsigned):
##             if isinstance(rhs.vhd, vhd_unsigned) and \
##                (lhs.vhd.size == rhs.vhd.size):
##                 pass
##             else:
##                 convOpen, convClose = "to_unsigned(", ", %s)" % lhs.vhd.size
##                 rhs.vhd = vhd_int()
##         elif isinstance(lhs.vhd, vhd_signed):
##             if isinstance(rhs.vhd, vhd_signed) and \
##                    (lhs.vhd.size == rhs.vhd.size):
##                 pass
##             else:
##                 convOpen, convClose = "to_signed(", ", %s)" % lhs.vhd.size
##                 rhs.vhd = vhd_int()
##         elif isinstance(lhs.vhd, vhd_std_logic):
##             rhs.vhd = vhd_std_logic()
        if isinstance(lhs.vhd, vhd_type):
            rhs.vhd = lhs.vhd
        self.visit(node.nodes[0])
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' := ')
        self.write(convOpen)
        # node.expr.target = obj = self.getObj(node.nodes[0])
        self.visit(node.expr)
        self.write(convClose)
        self.write(';')

    def visitAssName(self, node, *args):
        self.write(node.name)

    def visitAugAssign(self, node, *args):
        opmap = {"+=" : "+",
                 "-=" : "-",
                 "*=" : "*",
                 "//=" : "/",
                 "%=" : "mod",
                 "**=" : "**",
                 "|=" : "or",
                 ">>=" : ">>>",
                 "<<=" : "<<",
                 "&=" : "and",
                 "^=" : "xor"
                 }
        if node.op not in opmap:
            self.raiseError(node, _error.NotSupported,
                            "augmented assignment %s" % node.op)
        op = opmap[node.op]
        # XXX apparently no signed context required for augmented assigns
        self.visit(node.node)
        self.write(" := ")
        self.visit(node.node)
        self.write(" %s " % op)
        self.visit(node.expr)
        self.write(";")
         
    def visitBreak(self, node, *args):
        # self.write("disable %s;" % self.labelStack[-2])
        self.write("exit;")

    def visitCallFunc(self, node, *args):
        fn = node.node
        assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        opening, closing = '(', ')'
        sep = ", "
        if f is bool:
            self.write("(")
            arg = node.args[0]
            self.visit(arg)
            if isinstance(arg, vhd_std_logic):
                test = "'0'"
            else:
                test = "0"
            self.write(" /= %s)" % test)
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
            pre, post = "", ""
            if isinstance(node.vhd, vhd_unsigned):
                pre, post = "to_unsigned(", ", %s)" % node.vhd.size
            elif isinstance(node.vhd, vhd_signed):
                pre, post = "to_signed(", ", %s)" % node.vhd.size
            self.write(pre)
            self.visit(node.args[0])
            self.write(post)
            return
        elif type(f) is ClassType and issubclass(f, Exception):
            self.write(f.__name__)
        elif f in (posedge, negedge):
            opening, closing = ' ', ''
            self.write(f.__name__)
        elif f is delay:
            self.visit(node.args[0])
            self.write(" ns")
            return
        elif f is concat:
            sep = " & "
        elif hasattr(node, 'ast'):
            self.write(node.ast.name)
        else:
            self.write(f.__name__)
        if node.args:
            self.write(opening)
            self.visit(node.args[0], *args)
            for arg in node.args[1:]:
                self.write(sep)
                self.visit(arg, *args)
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
        if isinstance(node.vhd, vhd_std_logic):
            self.write("to_std_logic")
        self.write("(")
        self.visit(node.expr, context)
        op, code = node.ops[0]
        if op == "==":
            op = "="
        elif op == "!=":
            op = "/="
        self.write(" %s " % op)
        self.visit(code, context)
        self.write(")")

    def visitConst(self, node, context=None, *args):
        if context == _context.PRINT:
            self.write('"%s"' % node.value)
        else:
            if isinstance(node.vhd, vhd_std_logic):
                self.write("'%s'" % node.value)
##                     elif target._type is intbv:
##                         self.write('"%s"' % bin(node.value, len(target)))
            elif isinstance(node.vhd, vhd_boolean):
                self.write("%s" % bool(node.value))
            elif isinstance(node.vhd, (vhd_unsigned, vhd_signed)):
                self.write('"%s"' % bin(node.value, node.vhd.size))
            else:
                self.write(node.value)

    def visitContinue(self, node, *args):
        # self.write("next %s;" % self.labelStack[-1])
        self.write("next;")

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
            op = 'to'
            oneoff = ''
            if len(args) == 1:
                start, stop, step = None, args[0], None
            elif len(args) == 2:
                start, stop, step = args[0], args[1], None
            else:
                start, stop, step = args
        else: # downrange
            cmp = '>='
            op = 'downto'
            oneoff ='-1'
            if len(args) == 1:
                start, stop, step = args[0], None, None
            elif len(args) == 2:
                start, stop, step = args[0], args[1], None
            else:
                start, stop, step = args
        assert step is None
 ##        if node.breakLabel.isActive:
##             self.write("begin: %s" % node.breakLabel)
##             self.writeline()
##         if node.loopLabel.isActive:
##             self.write("%s: " % node.loopLabel)
        self.write("for %s in " % var)
        if start is None:
            self.write("0")
        else:
            self.visit(start)
            if f is downrange:
                self.write("-1")
        self.write(" %s " % op)
        if stop is None:
            self.write("0")
        else:
            self.visit(stop)
            if f is range:
                self.write("-1")
        self.write(" loop")
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end loop;")
##         if node.breakLabel.isActive:
##             self.writeline()
##             self.write("end")
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
                self.visit(node.expr)
            elif node.attrname == 'posedge':
                self.write("rising_edge(")
                self.visit(node.expr)
                self.write(")")
            elif node.attrname == 'negedge':
                self.write("falling_edge(")
                self.visit(node.expr)
                self.write(")")
            else:
                assert False
        elif isinstance(obj, EnumType):
            assert hasattr(obj, node.attrname)
            e = getattr(obj, node.attrname)
            self.write(e._toVHDL())

    def visitIf(self, node, *args):
        if node.ignore:
            return
        if node.isCase:
            self.mapToCase(node, *args)
        else:
            self.mapToIf(node, *args)

    def mapToCase(self, node, *args):
        var = node.caseVar
        self.write("case ")
        self.visit(var)
        self.write(" is")
        self.indent()
        for test, suite in node.tests:
            self.writeline()
            item = test.ops[0][1].obj
            self.write("when ")
            self.write(item._toVHDL())
            self.write(" =>")
            self.indent()
            self.visit(suite)
            self.dedent()
        if node.else_:
            self.writeline()
            self.write("when others =>")
            self.indent()
            self.visit(node.else_)
            self.dedent()
        self.dedent()
        self.writeline()
        self.write("end case;")
        
    def mapToIf(self, node, *args):
        first = True
        for test, suite in node.tests:
            if first:
                ifstring = "if "
                first = False
            else:
                ifstring = "elsif "
                self.writeline()
            self.write(ifstring)
            self.visit(test, _context.BOOLEAN)
            self.write(" then")
            self.indent()
            self.visit(suite)
            self.dedent()
        if node.else_:
            self.writeline()
            edges = self.getEdge(node.else_)
            if edges is not None:
                edgeTests = [e._toVHDL() for e in edges]
                self.write("elsif ")
                self.write("or ".join(edgeTests))
                self.write(" then")
            else:
                self.write("else")
            self.indent()
            self.visit(node.else_)
            self.dedent()
        self.writeline()
        self.write("end if;")

    def visitKeyword(self, node, *args):
        self.visit(node.expr)

    def visitModule(self, node, *args):
        for stmt in node.node.nodes:
            self.visit(stmt)
       
    def visitName(self, node, context=None, *args):
        n = node.name
        if n == 'False':
            if isinstance(node.vhd, vhd_std_logic):
                s = "'0'"
            else:
                s = "False"
        elif n == 'True':
            if isinstance(node.vhd, vhd_std_logic):
                s = "'1'"
            else:
                s = "True"
        elif n in self.ast.vardict:
            s = n
            obj = self.ast.vardict[n]
            vhd = inferVhdlObj(obj)
            if isinstance(vhd, vhd_unsigned):
                if isinstance(node.vhd, vhd_int):
                    s = "to_integer(%s)" % n
                elif isinstance(node.vhd, vhd_unsigned):
                    if vhd.size != node.vhd.size:
                        s = "resize(%s, %s)" % (n, node.vhd.size)
                else:
                    raise NotImplementedError

                
            elif isinstance(vhd, vhd_std_logic) and isinstance(node.vhd, vhd_boolean):
                s = "(%s = '1')" %  n
            elif isinstance(vhd, vhd_int):
                if isinstance(node.vhd, vhd_unsigned):
                    s = "to_unsigned(%s, %s)" % (n, node.vhd.size)
                elif isinstance(node.vhd, vhd_signed):
                    s = "to_signed(%s, %s)" % (n, node.vhd.size)
             
        elif n in self.ast.argnames:
            assert n in self.ast.symdict
            obj = self.ast.symdict[n]
            vhd = inferVhdlObj(obj)
            if isinstance(vhd, vhd_std_logic) and isinstance(node.vhd, vhd_boolean):
                s = "(%s = '1')" %  n
            else:
                s = n
        elif n in self.ast.symdict:
            obj = self.ast.symdict[n]
            s = n
            if isinstance(obj, bool):
                s = "'%s'" % int(obj)
            elif isinstance(obj, (int, long)):
                if isinstance(node.vhd, vhd_int):
                    s = "%s" % int(obj)
                elif isinstance(node.vhd, vhd_std_logic):
                    s = "'%s'" % int(obj)
                else:
                    s = '"%s"' % bin(obj, node.vhd.size)
            elif isinstance(obj, Signal):
                if context == _context.PRINT:
                    if obj._type is intbv:
                        s = "write(L, to_integer(%s))" % str(obj)
                    elif obj._type is bool:
                        s = "write(L, to_bit(%s))" % str(obj)
                    else:
                        typename = "UNDEF"
                        if isinstance(obj._val, EnumItemType):
                            typename = obj._val._type._name
                        s = "write(L, %s'image(%s))" % (typename, str(obj))
                else:
                    vhd = inferVhdlObj(obj)
                    n = s = str(obj)
                    if isinstance(vhd, vhd_unsigned):
                        if isinstance(node.vhd, vhd_int):
                            s = "to_integer(%s)" % n
                        elif isinstance(node.vhd, vhd_unsigned):
                            if vhd.size != node.vhd.size:
                                s = "resize(%s, %s)" % (n, node.vhd.size)
                        elif isinstance(node.vhd, vhd_boolean):
                            s = "(%s /= 0)" % n
                        else:
                            print node.vhd
                            raise NotImplementedError


                    elif isinstance(vhd, vhd_std_logic) and isinstance(node.vhd, vhd_boolean):
                        s = "(%s = '1')" %  n
                    elif isinstance(vhd, vhd_int):
                        if isinstance(node.vhd, (vhd_unsigned, vhd_signed)):
                            s = "to_unsigned(%s, %s)" % (n, node.vhd.size)
                        elif isinstance(node.vhd, vhd_signed):
                            s = "to_signed(%s, %s)" % (n, node.vhd.size)
                        else:
                            raise NotImplementedError
                    else:
                        s = str(obj)
            elif _isMem(obj):
                m = _getMemInfo(obj)
                assert m.name
                if not m.decl:
                    self.raiseError(node, _error.ListElementNotUnique, m.name)
                s = m.name
            elif isinstance(obj, EnumItemType):
                s = obj._toVHDL()
            elif type(obj) is ClassType and issubclass(obj, Exception):
                s = n
            else:
                self.raiseError(node, _error.UnsupportedType, "%s, %s" % (n, type(obj)))
        else:
            raise AssertionError("name ref: %s" % n)
        self.write(s)

    def visitPass(self, node, *args):
        self.write("null;")

    def handlePrint(self, node):
        assert len(node.nodes) == 1
        s = node.nodes[0]
        self.visit(s, _context.PRINT)
        self.write(';')
        self.writeline()
        self.write("writeline(output, L);")
        
    
    def visitPrint(self, node, *args):
        self.handlePrint(node)

    def visitPrintnl(self, node, *args):
        self.handlePrint(node)
    
    def visitRaise(self, node, *args):
#        pass
        self.write('assert False report "End of Simulation" severity Failure;')
##         self.write('$display("')
##         self.visit(node.expr1)
##         self.write('");')
##         self.writeline()
##         self.write("$finish;")
        
    def visitReturn(self, node, *args):
        self.write("disable %s;" % self.returnLabel)

    def visitSlice(self, node, context=None, *args):
        if isinstance(node.expr, astNode.CallFunc) and \
           node.expr.node.obj is intbv:
            c = self.getVal(node)
            pre, post = "", ""
            if isinstance(node.vhd, vhd_unsigned):
                print "YES"
                pre, post = "to_unsigned(", ", %s)" % node.vhd.size
            elif isinstance(node.vhd, vhd_signed):
                pre, post = "to_signed(", ", %s)" % node.vhd.size
            self.write(pre)
            self.write("%s" % c._val)
            self.write(post)
            return
        self.visit(node.expr)
        # special shortcut case for [:] slice
        if node.lower is None and node.upper is None:
            return
        self.write("(")
        if node.lower is None:
            self.write("%s" % node.obj._nrbits)
        else:
            self.visit(node.lower)
        self.write("-1 downto ")
        if node.upper is None:
            self.write("0")
        else:
            self.visit(node.upper)
        self.write(")")

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
        self.write("(")
        assert len(node.subs) == 1
        self.visit(node.subs[0])
        self.write(")")
        if addSignBit:
            self.write("})")

    def visitTuple(self, node, context=None, *args):
        assert context != None
        sep = ", "
        tpl = node.nodes
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(sep)
            self.visit(elt)

    def visitWhile(self, node, *args):
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.write("while ")
        self.visit(node.test)
        self.write(" loop")
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end loop")
        self.write(";")
        self.labelStack.pop()
        self.labelStack.pop()
        
    def visitYield(self, node, *args):
        self.write("wait ")
        yieldObj = self.getObj(node.value)
        if isinstance(yieldObj, delay):
            self.write("for ")
        elif isinstance(yieldObj, _WaiterList):
            self.write("until ")
        else:
            self.write("on ")
        self.visit(node.value, _context.YIELD)
        self.write(";")

    def manageEdges(self, ifnode, senslist):
        """ Helper method to convert MyHDL style template into VHDL style"""
        first = senslist[0]
        if isinstance(first, _WaiterList):
            bt = _WaiterList
        elif isinstance(first, Signal):
            bt = Signal
        elif isinstance(first, delay):
            bt  = delay
        assert bt
        for e in senslist:
            if not isinstance(e, bt):
                self.raiseError(node, "base type error in sensitivity list")
        if len(senslist) >= 2 and bt == _WaiterList:
            # ifnode = node.code.nodes[0]
            assert isinstance(ifnode, astNode.If)
            asyncEdges = []
            for test, suite in ifnode.tests:
                e = self.getEdge(test)
                if e is None:
                    self.raiseError(ifnode, "no edge test")
                asyncEdges.append(e)
            if ifnode.else_ is None:
                self.raiseError(ifnode, "no else test")
            edges = []
            for s in senslist:
                for e in asyncEdges:
                    if s is e:
                        break
                else:
                    edges.append(s)
            ifnode.else_.edge = edges
            senslist = [s.sig for s in senslist]
        return senslist

            
class _ConvertAlwaysVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        w = node.code.nodes[-1]
        y = w.body.nodes[0]
        if isinstance(y, astNode.Discard):
            y = y.expr
        assert isinstance(y, astNode.Yield)
        senslist = y.senslist
        senslist = self.manageEdges(w.body.nodes[1], senslist)
        singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
        self.write("%s: process (" % self.ast.name)
        if singleEdge:
            self.write(senslist[0].sig)
        else:
            for e in senslist[:-1]:
                self.write(e)
                self.write(', ')
            self.write(senslist[-1])
        self.write(") is")
        self.indent()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        if singleEdge:
            self.writeline()
            self.write("if %s then" % senslist[0]._toVHDL())
            self.indent()
        assert isinstance(w.body, astNode.Stmt)
        for stmt in w.body.nodes[1:]:
            self.writeline()
            self.visit(stmt)
        self.dedent()
        if singleEdge:
            self.writeline()
            self.write("end if;")
            self.dedent()
        self.writeline()
        self.write("end process %s;" % self.ast.name)
        self.writeline(2)
        
    
class _ConvertInitialVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("%s: process is" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        self.visit(node.code)
        self.writeline()
        self.write("wait;")
        self.dedent()
        self.writeline()
        self.write("end process %s;" % self.ast.name)
        self.writeline(2)


class _ConvertAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        senslist = self.ast.senslist
        self.write("%s: process (" % self.ast.name)
        for e in senslist[:-1]:
            self.write(e)
            self.write(', ')
        self.write(senslist[-1])
        self.write(") is")
        self.indent()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end process %s;" % self.ast.name)
        self.writeline(2)

        
class _ConvertSimpleAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitAssAttr(self, node, *args):
        self.visit(node.expr)
        self.isSigAss = True

    def visitFunction(self, node, *args):
        self.visit(node.code)
        self.writeline(2)


        
class _ConvertAlwaysDecoVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        assert self.ast.senslist
        senslist = self.ast.senslist
        senslist = self.manageEdges(node.code.nodes[0], senslist)
##         first = senslist[0]
##         if isinstance(first, _WaiterList):
##             bt = _WaiterList
##         elif isinstance(first, Signal):
##             bt = Signal
##         elif isinstance(first, delay):
##             bt  = delay
##         assert bt
##         for e in senslist:
##             if not isinstance(e, bt):
##                 self.raiseError(node, "base type error in sensitivity list")
##         if len(senslist) >= 2 and bt == _WaiterList:
##             ifnode = node.code.nodes[0]
##             assert isinstance(ifnode, astNode.If)
##             asyncEdges = []
##             for test, suite in ifnode.tests:
##                 e = self.getEdge(test)
##                 if e is None:
##                     self.raiseError(node, "no edge test")
##                 asyncEdges.append(e)
##             if ifnode.else_ is None:
##                 self.raiseError(node, "no else test")
##             edges = []
##             for s in senslist:
##                 for e in asyncEdges:
##                     if s is e:
##                         break
##                 else:
##                     edges.append(s)
##             ifnode.else_.edge = edges
##             senslist = [s.sig for s in senslist]    
        singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
        self.write("%s: process (" % self.ast.name)
        if singleEdge:
            self.write(senslist[0].sig)
        else:
            for e in senslist[:-1]:
                self.write(e)
                self.write(', ')
            self.write(senslist[-1])
        self.indent()
        self.writeDeclarations()
        self.dedent()
        self.write(") is")
        self.writeline()
        self.write("begin")
        self.indent()
        if singleEdge:
            self.writeline()
            self.write("if %s then" % senslist[0]._toVHDL())
            self.indent()
        self.visit(node.code)
        self.dedent()
        if singleEdge:
            self.writeline()
            self.write("end if;")
            self.dedent()
        self.writeline()
        self.write("end process %s;" % self.ast.name)
        self.writeline(2)
       
    
class _ConvertFunctionVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnObj = ast.returnObj
        self.returnLabel = _Label("RETURN")

    def writeOutputDeclaration(self):
        self.write(self.ast.vhd.toStr(constr=False))

    def writeInputDeclarations(self):
        endchar = ""
        for name in self.ast.argnames:
            self.write(endchar)
            enchar = ";"
            obj = self.ast.symdict[name]
            self.writeline()
            self.writeDeclaration(obj, name, dir="in", constr=False, endchar="")
            
    def visitFunction(self, node, *args):
        self.write("function %s(" % self.ast.name)
        self.indent()
        self.writeInputDeclarations()
        self.writeline()
        self.write(") return ")
        self.writeOutputDeclaration()
        self.write(" is")
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end function %s;" % self.ast.name)
        self.writeline(2)

    def visitReturn(self, node, *args):
        self.write("return ")
        self.visit(node.value)
        self.write(";")
    
    
class _ConvertTaskVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnLabel = _Label("RETURN")

    def writeInterfaceDeclarations(self):
        endchar = ""
        for name in self.ast.argnames:
            self.write(endchar)
            endchar = ";"
            obj = self.ast.symdict[name]
            output = name in self.ast.outputs
            input = name in self.ast.inputs
            inout = input and output
            dir = (inout and "inout") or (output and "out") or "in"
            self.writeline()
            self.writeDeclaration(obj, name, dir=dir, constr=False, endchar="")
            
    def visitFunction(self, node, *args):
        self.write("procedure %s" % self.ast.name)
        if self.ast.argnames:
            self.write("(")
            self.indent()
            self.writeInterfaceDeclarations()
            self.write(") ")
        self.write("is")
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        t = node.code.nodes[0].tests[0][0]
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end procedure %s;" % self.ast.name)
        self.writeline(2)


class vhd_type(object):
    def __init__(self, size=0):
        self.size = size
        
class vhd_std_logic(vhd_type):
    def __init__(self, size=0):
        self.size = 1
    def toStr(self, constr=True):
        return 'std_logic'
        
class vhd_boolean(vhd_type):
    def __init__(self, size=0):
        self.size = 1
    def toStr(self, constr=True):
        return 'boolean'

class vhd_vector(vhd_type):
    pass
    
class vhd_unsigned(vhd_vector):
    def toStr(self, constr=True):
        if constr:
            return "unsigned(%s downto 0)" % (self.size-1)
        else:
            return "unsigned"
    
class vhd_signed(vhd_vector):
    def toStr(self, constr=True):
        if constr:
            return "signed(%s downto 0)" % (self.size-1)
        else:
            return "signed"
    
class vhd_int(vhd_type):
    def toStr(self, constr=True):
        return "integer"

class _loopInt(int):
    pass

def maxType(o1, o2):
    s1 = s2 = 0
    if isinstance(o1, vhd_type):
        s1 = o1.size
    if isinstance(o2, vhd_type):
        s2 = o2.size
    s = max(s1, s2)
    if isinstance(o1, vhd_signed) or isinstance(o2, vhd_signed):
        return vhd_signed(s)
    elif isinstance(o1, vhd_unsigned) or isinstance(o2, vhd_unsigned):
        return vhd_unsigned(s)
    elif isinstance(o1, vhd_std_logic) or isinstance(o2, vhd_std_logic):
        return vhd_std_logic()
    elif isinstance(o1, vhd_int) or isinstance(o2, vhd_int):
        return vhd_int()
    else:
        return None
    
def inferVhdlObj(obj):
    vhd = None
    if (isinstance(obj, Signal) and obj._type is intbv) or \
       isinstance(obj, intbv):
        if obj.min < 0:
            vhd = vhd_signed(len(obj))
        else:
            vhd = vhd_unsigned(len(obj))
    elif (isinstance(obj, Signal) and obj._type is bool) or \
         isinstance(obj, bool):
        vhd = vhd_std_logic()
    elif isinstance(obj, (int, long)):
        vhd = vhd_int()
    return vhd

        
class _AnnotateTypesVisitor(_ConversionMixin):

    def __init__(self, ast):
        self.ast = ast

    def visitAssAttr(self, node):
        self.visit(node.expr)
        node.vhd = node.expr.vhd
        
    def visitCallFunc(self, node, *args):
        fn = node.node
        assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        node.vhd = inferVhdlObj(node.obj)
        self.visitChildNodes(node)
        if f is concat:
            s = 0
            for a in node.args:
                s += a.vhd.size
            node.vhd = vhd_unsigned(s)
        elif f is int:
            node.vhd = vhd_int()
            node.args[0].vhd = vhd_int()
        elif f is intbv:
            node.vhd = vhd_int()
        elif f is len:
            node.vhd = vhd_int()
        elif hasattr(node, 'ast'):
            v = _AnnotateTypesVisitor(node.ast)
            compiler.walk(node.ast, v)
            node.vhd = node.ast.vhd = inferVhdlObj(node.ast.returnObj)
    
    def visitCompare(self, node):
        node.vhd = vhd_boolean()
        self.visitChildNodes(node)
        expr = node.expr
        op, code = node.ops[0]
        o = maxType(expr.vhd, code.vhd)
        if isinstance(o, vhd_std_logic):
            expr.vhd = code.vhd = o

    def visitConst(self, node):
        node.vhd = vhd_int()

    def visitFor(self, node):
        self.visitChildNodes(node)
        var = node.assign.name
        # make it possible to detect loop variable
        self.ast.vardict[var] = _loopInt()

    def visitGetattr(self, node):
        self.visitChildNodes(node)
        node.vhd = node.expr.vhd
        
    def visitName(self, node):
        node.vhd = inferVhdlObj(node.obj)
 
    # visitAssName = visitName
    def visitAssName(self, node):
        node.obj = self.ast.vardict[node.name]
        self.visitName(node)
        
        
    def binaryOp(self, node, op=None):
        self.visit(node.left)
        self.visit(node.right)
        r, l = node.right.vhd, node.left.vhd
        rs, ls = r.size, l.size
        if isinstance(r, vhd_signed) and isinstance(r, vhd_unsigned):
            rs += 1
        if isinstance(r, vhd_unsigned) and isinstance(r, vhd_signed):
            ls += 1
        if isinstance(r, vhd_vector) and isinstance(l, vhd_vector):
            if op in ('+', '-'):
                s = max(ls, rs)
            elif op == '%':
                s = rs
            elif op == '/':
                s = ls
            elif op == '*':
                s = ls + rs
            else:
                self.raiseError(node, "Not implemented: %s" % op)
        elif isinstance(l, vhd_vector) and isinstance(r, vhd_int):
            if op in ('+', '-', '%', '/'):
                s = ls
            elif op == '*':
                 s = 2 * ls
            else:
                self.raiseError(node, "Not implemented")
        elif isinstance(l, vhd_int) and isinstance(r, vhd_vector):
            if op in ('+', '-', '%', '/'):
                s = rs
            elif op == '*':
                s = 2 * rs
            else:
                self.raiseError(node, "Not implemented: %s" % op)
        if isinstance(r, vhd_int) and isinstance(l, vhd_int):
            node.vhd = vhd_int()
        elif isinstance(r, (vhd_signed, vhd_int)) and isinstance(l, (vhd_signed, vhd_int)):
            node.vhd = vhd_signed(s)
        elif isinstance(r, (vhd_unsigned, vhd_int)) and isinstance(l, (vhd_unsigned, vhd_int)):
            node.vhd = vhd_unsigned(s)
        else:
            node.vhd = vhd_int()
        node.vhdOri = node.vhd

    def visitAdd(self, node):
        self.binaryOp(node, op='+')
    def visitSub(self, node):
        self.binaryOp(node, op='-')
    def visitMod(self, node):
        self.binaryOp(node, op='%')
    def visitMul(self, node):
        self.binaryOp(node, op='*')
    def visitFloorDiv(self, node):
        self.binaryOp(node, op='/')

    
    def multiBitOp(self, node):
        self.visitChildNodes(node)
        o = None
        for n in node.nodes:
            o = maxType(o, n.vhd)
        for n in node.nodes:
            n.vhd = o
        node.vhd = o
    visitBitand = visitBitor = visitBitxor = multiBitOp

    def multiBoolOp(self, node):
        self.visitChildNodes(node)
        for n in node.nodes:
            n.vhd = vhd_boolean()
        node.vhd = vhd_boolean()
    visitAnd = visitOr = multiBoolOp

    def visitNot(self, node):
        self.visit(node.expr)
        node.vhd = node.expr.vhd = vhd_boolean()

    def visitIf(self, node):
        self.visitChildNodes(node)
        for test, suite in node.tests:
            test.vhd = vhd_boolean()

    def shift(self, node):
        self.visitChildNodes(node)
        node.vhd = node.left.vhd
        node.right.vhd = vhd_int()
    visitRightShift = visitLeftShift = shift

    def visitSlice(self, node):
        self.visitChildNodes(node)
        lower = 0
        t = vhd_unsigned
        if hasattr(node.expr, 'vhd'):
            lower = node.expr.vhd.size
            t = type(node.expr.vhd)
        if node.lower:
            lower = self.getVal(node.lower)
        upper  = 0
        if node.upper:
            upper = self.getVal(node.upper)
        node.vhd = t(lower-upper)

    def visitSubscript(self, node):
        self.visitChildNodes(node)
        node.vhd = vhd_std_logic()
        
    def unaryOp(self, node):
        self.visit(node.expr)
        node.vhd = node.expr.vhd

    visitUnaryAdd = visitUnarySub = unaryOp

    def visitWhile(self, node):
        self.visitChildNodes(node)
        node.test.vhd = vhd_boolean()
        
        


def _annotateTypes(genlist):
    for ast in genlist:
        v = _AnnotateTypesVisitor(ast)
        compiler.walk(ast, v)



    

    
 
