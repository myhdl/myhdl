#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
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


import sys
import os
import math
import traceback
import inspect
from datetime import datetime
import compiler
# from compiler import ast as astNode
import ast

from types import GeneratorType, FunctionType, ClassType, TypeType, StringType
from cStringIO import StringIO
import __builtin__
import warnings

import myhdl
from myhdl import *
from myhdl import ToVerilogError, ToVerilogWarning
from myhdl._extractHierarchy import (_HierExtr, _isMem, _getMemInfo,
                                     _UserVerilog, _userCodeMap)

from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl._instance import _Instantiator
from myhdl.conversion._misc import (_error, _access, _kind, _context, 
                                    _ConversionMixin, _Label, _genUniqueSuffix, _isConstant)
from myhdl.conversion._analyze import (_analyzeSigs, _analyzeGens, _analyzeTopFunc, 
                                       _Ram, _Rom)
from myhdl._Signal import _Signal
            
_converting = 0
_profileFunc = None

def _checkArgs(arglist):
    for arg in arglist:
        if not isinstance(arg, (GeneratorType, _Instantiator, _UserVerilog)):
            raise ToVerilogError(_error.ArgType, arg)
        
def _flatten(*args):
    arglist = []
    for arg in args:
        if id(arg) in _userCodeMap['verilog']:
            arglist.append(_userCodeMap['verilog'][id(arg)])
        elif isinstance(arg, (list, tuple, set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist

def _makeDoc(doc, indent=''):
    if doc is None:
        return ''
    pre = indent + '// '
    doc = pre + doc
    pre = '\n' + pre
    doc = doc.replace('\n', pre)
    doc = doc + '\n'
    return doc


class _ToVerilogConvertor(object):

    __slots__ = ("name", 
                 "timescale", 
                 "standard",
                 "prefer_blocking_assignments", 
                 "radix",
                 "header"
                 )

    def __init__(self):
        self.name = None
        self.timescale = "1ns/10ps"
        self.standard = '2001'
        self.prefer_blocking_assignments = False
        self.radix = ''
        self.header = ''

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
        
        ### initialize properly ###
        _genUniqueSuffix.reset()

        siglist, memlist = _analyzeSigs(h.hierarchy)
        arglist = _flatten(h.top)
        # print h.top
        _checkArgs(arglist)
        genlist = _analyzeGens(arglist, h.absnames)
        intf = _analyzeTopFunc(func, *args, **kwargs)
        intf.name = name
        doc = _makeDoc(inspect.getdoc(func))

        _writeFileHeader(vfile, vpath, self.timescale)
        _writeModuleHeader(vfile, intf, doc)
        _writeSigDecls(vfile, intf, siglist, memlist)
        _convertGens(genlist, vfile)
        _writeModuleFooter(vfile)

        vfile.close()

        # don't write testbench if module has no ports
        if len(intf.argnames) > 0:
            tbpath = "tb_" + vpath
            tbfile = open(tbpath, 'w')
            _writeTestBench(tbfile, intf)
            tbfile.close()

        # clean up signal names
        for sig in siglist:
            sig._clear()
#             sig._name = None
#             sig._driven = False
#             sig._read = False
            
        # clean up attributes
        self.name = None
        self.standard = '2001'
        self.prefer_blocking_assignments = False
        self.radix = ''
        self.header = ""
        
        return h.top
    

toVerilog = _ToVerilogConvertor()

default_header = """\
// File: %(filename)s
// Generated by MyHDL %(version)s
// Date: %(date)s
"""

def _writeFileHeader(f, fn, ts):
    vars = dict(filename=fn, 
                version=myhdl.__version__,
                date=datetime.today().ctime()
                )
    header = default_header
    if toVerilog.header:
        header = toVerilog.header
    print >> f, header % vars
    print >> f
    print >> f, "`timescale %s" % ts
    print >> f


def _writeModuleHeader(f, intf, doc):
    print >> f, "module %s (" % intf.name
    b = StringIO()
    for portname in intf.argnames:
        print >> b, "    %s," % portname
    print >> f, b.getvalue()[:-2]
    b.close()
    print >> f, ");"
    print >> f, doc
    print >> f
    for portname in intf.argnames:
        s = intf.argdict[portname]
        if s._name is None:
            raise ToVerilogError(_error.ShadowingSignal, portname)
        if s._inList:
            raise ToVerilogError(_error.PortInList, portname)
        # make sure signal name is equal to its port name
        s._name = portname
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            if s._read:
                warnings.warn("%s: %s" % (_error.OutputPortRead, portname),
                              category=ToVerilogWarning
                              )
            print >> f, "output %s%s%s;" % (p, r, portname)
            if s._driven == 'reg':
                print >> f, "reg %s%s%s;" % (p, r, portname)
            else:
                print >> f, "wire %s%s%s;" % (p, r, portname)
        else:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedPort, portname),
                              category=ToVerilogWarning
                              )
            print >> f, "input %s%s%s;" % (p, r, portname)
    print >> f


def _writeSigDecls(f, intf, siglist, memlist):
    constwires = []
    for s in siglist:
        if not s._used:
            continue
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedSignal, s._name),
                              category=ToVerilogWarning
                              )
            k = 'wire'
            if s._driven == 'reg':
                k = 'reg'
            # the following line implements initial value assignments
            # print >> f, "%s %s%s = %s;" % (k, r, s._name, int(s._val))
            print >> f, "%s %s%s%s;" % (k, p, r, s._name)
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
        if not m._used:
            continue
        r = _getRangeString(m.elObj)
        p = _getSignString(m.elObj)
        k = 'reg'
        if m.mem[0]._driven == 'wire':
            k = 'wire'
        print >> f, "%s %s%s%s [0:%s-1];" % (k, p, r, m.name, m.depth)
    print >> f
    for s in constwires:
        print >> f, "assign %s = %s;" % (s._name, int(s._val))
    print >> f
    # shadow signal assignments
    for s in siglist:
        if hasattr(s, 'toVerilog'):
            print >> f, s.toVerilog()
    print >> f


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
    for tree in genlist:
        if isinstance(tree, _UserVerilog):
            blockBuf.write(str(tree))
            continue
        if tree.kind == _kind.ALWAYS:
            Visitor = _ConvertAlwaysVisitor
        elif tree.kind == _kind.INITIAL:
            Visitor = _ConvertInitialVisitor
        elif tree.kind == _kind.SIMPLE_ALWAYS_COMB:
            Visitor = _ConvertSimpleAlwaysCombVisitor
        elif tree.kind == _kind.ALWAYS_DECO:
            Visitor = _ConvertAlwaysDecoVisitor
        else: # ALWAYS_COMB
            Visitor = _ConvertAlwaysCombVisitor
        v = Visitor(tree, blockBuf, funcBuf)
        v.visit(tree)
    vfile.write(funcBuf.getvalue()); funcBuf.close()
    vfile.write(blockBuf.getvalue()); blockBuf.close()


opmap = {
    ast.Add      : '+',
    ast.Sub      : '-',
    ast.Mult     : '*',
    ast.Div      : '/',
    ast.Mod      : '%',
    ast.Pow      : '**',
    ast.LShift   : '<<',
    ast.RShift   : '>>>',
    ast.BitOr    : '|',
    ast.BitAnd   : '&',
    ast.BitXor   : '^',
    ast.FloorDiv : '/',
    ast.Invert   : '~',
    ast.Not      : '!',
    ast.UAdd     : '+',
    ast.USub     : '-',
    ast.Eq       : '==',
    ast.Gt       : '>',
    ast.GtE      : '>=',
    ast.Lt       : '<',
    ast.LtE      : '<=',
    ast.NotEq    : '!=',
    ast.And      : '&&',
    ast.Or       : '||',
}



class _ConvertVisitor(ast.NodeVisitor, _ConversionMixin):
    
    def __init__(self, tree, buf):
        self.tree = tree
        self.buf = buf
        self.returnLabel = tree.name
        self.ind = ''
        self.isSigAss = False
        self.okSigAss = True
        self.labelStack = []
        self.context = _context.UNKNOWN

    def raiseError(self, node, kind, msg=""):
        lineno = self.getLineNo(node)
        info = "in file %s, line %s:\n    " % \
              (self.tree.sourcefile, self.tree.lineoffset+lineno)
        raise ToVerilogError(kind, msg, info)

    def write(self, arg):
        self.buf.write("%s" % arg)

    def writeline(self, nr=1):
        for i in range(nr):
            self.buf.write("\n%s" % self.ind)
            
    def writeDoc(self, node):
        doc = ast.get_docstring(node)
        doc = _makeDoc(doc)
        self.write(doc)
            
    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def IntRepr(self, n):
        # write size for large integers (beyond 32 bits signed)
        # with some safety margin
        # XXX signed indication 's' ???
        size = ''
        radix = ''
        num = str(n)
        if toVerilog.radix == "hex":
            radix = "'h"
            num = hex(n)[2:]
        if n >= 2**30:
            size = int(math.ceil(math.log(n+1,2))) + 1  # sign bit!
            if not radix:
                radix = "'d"
        return "%s%s%s" % (size, radix, num)

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
            if isinstance(obj, (intbv, _Signal)):
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
        for name, obj in self.tree.vardict.items():
            self.writeline()
            self.writeDeclaration(obj, name, "reg")

    def writeAlwaysHeader(self):
        assert self.tree.senslist
        senslist = self.tree.senslist
        self.write("always ")
        self.writeSensitivityList(senslist)
        self.write(" begin: %s" % self.tree.name)
        self.indent()

    def writeSensitivityList(self, senslist):
        sep = ', '
        if toVerilog.standard == '1995':
            sep = ' or '
        self.write("@(")
        for e in senslist[:-1]:
            self.write(e._toVerilog())
            self.write(sep)
        self.write(senslist[-1]._toVerilog())
        self.write(")")



#     def binaryOp(self, node, op=None):
#         context = None
#         if node.signed:
#             context = _context.SIGNED
#         self.write("(")
#         self.visit(node.left, context)
#         self.write(" %s " % op)
#         self.visit(node.right, context)
#         self.write(")")
#     def visitAdd(self, node, *args):
#         self.binaryOp(node, '+')
#     def visitFloorDiv(self, node, *args):
#         self.binaryOp(node, '/')
#     def visitLeftShift(self, node, *args):
#         self.binaryOp(node, '<<')
#     def visitMod(self, node, context=None, *args):
#         if context == _context.PRINT:
#             self.visit(node.left, _context.PRINT)
#             self.write(", ")
#             self.visit(node.right, _context.PRINT)
#         else:
#             self.binaryOp(node, '%')        
#     def visitMul(self, node, *args):
#         self.binaryOp(node, '*')
#     def visitPower(self, node, *args):
#          self.binaryOp(node, '**')
#     def visitSub(self, node, *args):
#         self.binaryOp(node, "-")
#     def visitRightShift(self, node, *args):
#         # Additional cast to signed of the full expression
#         # this is apparently required by cver - not sure if it
#         # is actually required by standard Verilog.
#         # It shouldn't hurt however.
#         if node.signed:
#             self.write("$signed")
#         self.binaryOp(node, '>>>')


    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and self.context == _context.PRINT:
            self.visit(node.left)
            self.write(", ")
            self.visit(node.right)
        else:
            if isinstance(node.op,  ast.RShift):
                # Additional cast to signed of the full expression
                # this is apparently required by cver - not sure if it
                # is actually required by standard Verilog.
                # It shouldn't hurt however.
                if node.signed:
                    self.write("$signed")
            self.context = None
            if node.signed:
                self.context = _context.SIGNED
            self.write("(")
            self.visit(node.left)
            self.write(" %s " % opmap[type(node.op)])
            self.visit(node.right)
            self.write(")")
            self.context = None




    def checkOpWithNegIntbv(self, node, op):
        if op in ("+", "-", "*", "~", "&&", "||", "!"):
            return
        if isinstance(node, astNode.Name):
            o = node.obj
            if isinstance(o, (_Signal, intbv)) and o.min is not None and o.min < 0:
                self.raiseError(node, _error.NotSupported,
                                "negative intbv with operator %s" % op)


#     def multiOp(self, node, op):
#         for n in node.nodes:
#             self.checkOpWithNegIntbv(n, op)
#         self.write("(")
#         self.visit(node.nodes[0])
#         for n in node.nodes[1:]:
#             self.write(" %s " % op)
#             self.visit(n)
#         self.write(")")
#     def visitAnd(self, node, *args):
#         self.multiOp(node, '&&')
#     def visitBitand(self, node, *args):
#         self.multiOp(node, '&')
#     def visitBitor(self, node, *args):
#         self.multiOp(node, '|')
#     def visitBitxor(self, node, *args):
#         self.multiOp(node, '^')
#     def visitOr(self, node, *args):
#         self.multiOp(node, '||')


    def visit_BoolOp(self, node):
        self.write("(")
        self.visit(node.values[0])
        for n in node.values[1:]:
            self.write(" %s " % opmap[type(node.op)])
            self.visit(n)
        self.write(")")
        



#     def unaryOp(self, node, op, context):
#         self.checkOpWithNegIntbv(node.expr, op)
#         self.write("(%s" % op)
#         self.visit(node.expr, context)
#         self.write(")")
#     def visitInvert(self, node, context=None, *args):
#         self.unaryOp(node, '~', context)
#     def visitNot(self, node, context=None, *args):
#         self.unaryOp(node, '!', context)
#     def visitUnaryAdd(self, node, context=None, *args):
#         self.unaryOp(node, '+', context)
#     def visitUnarySub(self, node, context=None, *args):
#         self.unaryOp(node, '-', context)


    def visit_UnaryOp(self, node):
        self.write("(%s" % opmap[type(node.op)])
        self.visit(node.operand)
        self.write(")")



#     def visitAssAttr(self, node, *args):
#         assert node.attrname == 'next'
#         self.isSigAss = True
#         self.visit(node.expr)

#     def visitGetattr(self, node, *args):
#         assert isinstance(node.expr, astNode.Name)
#         n = node.expr.name
#         if n in self.tree.symdict:
#             obj = self.tree.symdict[n]
#         elif n in self.tree.vardict:
#             obj = self.tree.vardict[n]
#         else:
#             raise AssertionError("object not found")
#         if isinstance(obj, Signal):
#             if node.attrname == 'next':
#                 self.isSigAss = True
#                 self.visit(node.expr)
#             elif node.attrname in ('posedge', 'negedge'):
#                 self.write(node.attrname)
#                 self.write(' ')
#                 self.visit(node.expr)
#             elif node.attrname == 'val':
#                 self.visit(node.expr)
#         if isinstance(obj, (Signal, intbv)):
#             if node.attrname in ('min', 'max'):
#                 self.write("%s" % node.obj)
#         if isinstance(obj, EnumType):
#             assert hasattr(obj, node.attrname)
#             e = getattr(obj, node.attrname)
#             self.write(e._toVerilog())


    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setAttr(node)
        else:
            self.getAttr(node)

    def setAttr(self, node):
        assert node.attr == 'next'
        self.isSigAss = self.okSigAss
        self.visit(node.value)

    def getAttr(self, node):
        assert isinstance(node.value, ast.Name)
        n = node.value.id
        if n in self.tree.symdict:
            obj = self.tree.symdict[n]
        elif n in self.tree.vardict:
            obj = self.tree.vardict[n]
        else:
            raise AssertionError("object not found")
        if isinstance(obj, _Signal):
            if node.attr == 'next':
                self.isSigAss = self.okSigAss
                self.visit(node.value)
            elif node.attr in ('posedge', 'negedge'):
                self.write(node.attr)
                self.write(' ')
                self.visit(node.value)
            elif node.attr == 'val':
                self.visit(node.value)
        if isinstance(obj, (_Signal, intbv)):
            if node.attr in ('min', 'max'):
                self.write("%s" % node.obj)
        if isinstance(obj, EnumType):
            assert hasattr(obj, node.attr)
            e = getattr(obj, node.attr)
            self.write(e._toVerilog())


#     def visitAssert(self, node, *args):
#         self.write("if (")
#         self.visit(node.test)
#         self.write(" !== 1) begin")
#         self.indent()
#         self.writeline()
#         self.write('$display("*** AssertionError ***");')
#         # self.writeline()
#         # self.write('$finish;')
#         self.dedent()
#         self.writeline()
#         self.write("end")

    def visit_Assert(self, node):
        self.write("if (")
        self.visit(node.test)
        self.write(" !== 1) begin")
        self.indent()
        self.writeline()
        self.write('$display("*** AssertionError ***");')
        # self.writeline()
        # self.write('$finish;')
        self.dedent()
        self.writeline()
        self.write("end")



#     def visitAssign(self, node, *args):
#         assert len(node.nodes) == 1
#         # shortcut for expansion of ROM in case statement
#         if isinstance(node.expr, astNode.Subscript) and \
#                isinstance(node.expr.expr.obj, _Rom):
#             rom = node.expr.expr.obj.rom
#             self.write("// synthesis parallel_case full_case")
#             self.writeline()
#             self.write("case (")
#             self.visit(node.expr.subs[0])
#             self.write(")")
#             self.indent()
#             for i, n in enumerate(rom):
#                 self.writeline()
#                 if i == len(rom)-1:
#                     self.write("default: ")
#                 else:
#                     self.write("%s: " % i)
#                 self.visit(node.nodes[0])
#                 if self.isSigAss:
#                     self.write(' <= ')
#                     self.isSigAss = False
#                 else:
#                     self.write(' = ')
#                 self.writeIntSize(n)
#                 self.write("%s;" % n)
#             self.dedent()
#             self.writeline()
#             self.write("endcase")
#             return
#         # default behavior
#         self.visit(node.nodes[0])
#         if self.isSigAss:
#             self.write(' <= ')
#             self.isSigAss = False
#         else:
#             self.write(' = ')
#         self.visit(node.expr)
#         self.write(';')



    def visit_Assign(self, node):
        # shortcut for expansion of ROM in case statement
        if isinstance(node.value, ast.Subscript) and \
                isinstance(node.value.slice, ast.Index) and\
                isinstance(node.value.value.obj, _Rom):
            rom = node.value.value.obj.rom
#            self.write("// synthesis parallel_case full_case")
#            self.writeline()
            self.write("case (")
            self.visit(node.value.slice)
            self.write(")")
            self.indent()
            for i, n in enumerate(rom):
                self.writeline()
                if i == len(rom)-1:
                    self.write("default: ")
                else:
                    self.write("%s: " % i)
                self.visit(node.targets[0])
                if self.isSigAss:
                    self.write(' <= ')
                    self.isSigAss = False
                else:
                    self.write(' = ')
                s = self.IntRepr(n)
                self.write("%s;" %s)
            self.dedent()
            self.writeline()
            self.write("endcase")
            return
        # default behavior
        self.visit(node.targets[0])
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' = ')
        self.visit(node.value)
        self.write(';')


#     def visitAugAssign(self, node, *args):
#         opmap = {"+=" : "+",
#                  "-=" : "-",
#                  "*=" : "*",
#                  "//=" : "/",
#                  "%=" : "%",
#                  "**=" : "**",
#                  "|=" : "|",
#                  ">>=" : ">>>",
#                  "<<=" : "<<",
#                  "&=" : "&",
#                  "^=" : "^"
#                  }
#         if node.op not in opmap:
#             self.raiseError(node, _error.NotSupported,
#                             "augmented assignment %s" % node.op)
#         op = opmap[node.op]
#         # XXX apparently no signed context required for augmented assigns
#         self.visit(node.node)
#         self.write(" = ")
#         self.visit(node.node)
#         self.write(" %s " % op)
#         self.visit(node.expr)
#         self.write(";")


    def visit_AugAssign(self, node, *args):
        # XXX apparently no signed context required for augmented assigns
        self.visit(node.target)
        self.write(" = ")
        self.visit(node.target)
        self.write(" %s " % opmap[type(node.op)])
        self.visit(node.value)
        self.write(";")



#     def visitBreak(self, node, *args):
#         self.write("disable %s;" % self.labelStack[-2])

    def visit_Break(self, node,):
        self.write("disable %s;" % self.labelStack[-2])





#     def visitCallFunc(self, node, *args):
#         fn = node.node
#         # assert isinstance(fn, astNode.Name)
#         f = self.getObj(fn)
#         opening, closing = '(', ')'
#         if f is bool:
#             self.write("(")
#             self.visit(node.args[0])
#             self.write(" != 0)")
#             # self.write(" ? 1'b1 : 1'b0)")
#             return
#         elif f is len:
#             val = self.getVal(node)
#             self.require(node, val is not None, "cannot calculate len")
#             self.write(`val`)
#             return
#         elif f is now:
#             self.write("$time")
#             return
#         elif f is ord:
#             opening, closing = '', ''
#             if isinstance(node.args[0], astNode.Const):
#                 if  type(node.args[0].value) != StringType:
#                     self.raiseError(node, _error.UnsupportedType, "%s" % (type(node.args[0].value)))
#                 elif len(node.args[0].value) > 1:
#                     self.raiseError(node, _error.UnsupportedType, "Strings with length > 1")
#                 else:
#                     node.args[0].value = ord(node.args[0].value)
#         elif f in (int, long):
#             opening, closing = '', ''
#             # convert number argument to integer
#             if isinstance(node.args[0], astNode.Const):
#                 node.args[0].value = int(node.args[0].value)
#         elif f is intbv:
#             self.visit(node.args[0])
#             return
#         elif f == intbv.signed: # note equality comparison
#             # comes from a getattr
#             opening, closing = '', ''
#             if not fn.expr.signed:
#                 opening, closing = "$signed(", ")"
#             self.write(opening)
#             self.visit(fn.expr)
#             self.write(closing)
#         elif type(f) in (ClassType, TypeType) and issubclass(f, Exception):
#             self.write(f.__name__)
#         elif f in (posedge, negedge):
#             opening, closing = ' ', ''
#             self.write(f.__name__)
#         elif f is concat:
#             opening, closing = '{', '}'
#         elif f is delay:
#             self.visit(node.args[0])
#             return
#         elif hasattr(node, 'tree'):
#             self.write(node.tree.name)
#         else:
#             self.write(f.__name__)
#         if node.args:
#             self.write(opening)
#             self.visit(node.args[0])
#             for arg in node.args[1:]:
#                 self.write(", ")
#                 self.visit(arg)
#             self.write(closing)
#         if hasattr(node, 'tree'):
#             if node.tree.kind == _kind.TASK:
#                 Visitor = _ConvertTaskVisitor
#             else:
#                 Visitor = _ConvertFunctionVisitor
#             v = Visitor(node.tree, self.funcBuf)
#             compiler.walk(node.tree, v)


    def visit_Call(self, node):
        self.context = None
        fn = node.func
        # assert isinstance(fn, astNode.Name)
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
        elif f is now:
            self.write("$time")
            return
        elif f is ord:
            opening, closing = '', ''
            if isinstance(node.args[0], ast.Str):
                if len(node.args[0].s) > 1:
                    self.raiseError(node, _error.UnsupportedType, "Strings with length > 1")
                else:
                    node.args[0].s = ord(node.args[0].s)
        elif f in (int, long):
            opening, closing = '', ''
            # convert number argument to integer
            if isinstance(node.args[0], ast.Num):
                node.args[0].n = int(node.args[0].n)
        elif f is intbv:
            self.visit(node.args[0])
            return
        elif f == intbv.signed: # note equality comparison
            # comes from a getattr
            opening, closing = '', ''
            if not fn.value.signed:
                opening, closing = "$signed(", ")"
            self.write(opening)
            self.visit(fn.value)
            self.write(closing)
        elif type(f) in (ClassType, TypeType) and issubclass(f, Exception):
            self.write(f.__name__)
        elif f in (posedge, negedge):
            opening, closing = ' ', ''
            self.write(f.__name__)
        elif f is concat:
            opening, closing = '{', '}'
        elif f is delay:
            self.visit(node.args[0])
            return
        elif hasattr(node, 'tree'):
            self.write(node.tree.name)
        else:
            self.write(f.__name__)
        if node.args:
            self.write(opening)
            self.visit(node.args[0])
            for arg in node.args[1:]:
                self.write(", ")
                self.visit(arg)
            self.write(closing)
        if hasattr(node, 'tree'):
            if node.tree.kind == _kind.TASK:
                Visitor = _ConvertTaskVisitor
            else:
                Visitor = _ConvertFunctionVisitor
            v = Visitor(node.tree, self.funcBuf)
            v.visit(node.tree)


#     def visitCompare(self, node, *args):
#         context = None
#         if node.signed:
#             context = _context.SIGNED
#         self.write("(")
#         self.visit(node.expr, context)
#         op, code = node.ops[0]
#         self.write(" %s " % op)
#         self.visit(code, context)
#         self.write(")")

    def visit_Compare(self, node):
        self.context = None
        if node.signed:
            self.context = _context.SIGNED
        self.write("(")
        self.visit(node.left)
        self.write(" %s " % opmap[type(node.ops[0])])
        self.visit(node.comparators[0])
        self.write(")")
        self.context = None



#     def visitConst(self, node, context=None, *args):
#         if context == _context.PRINT:
#             self.write('"%s"' % node.value)
#         else:
#             self.write(node.value)

    def visit_Num(self, node):
        if self.context == _context.PRINT:
            self.write('"%s"' % node.n)
        else:
            self.write(node.n)

    def visit_Str(self, node):
        if self.context == _context.PRINT:
            self.write('"%s"' % node.s)
        else:
            self.write(node.s)

#     def visitContinue(self, node, *args):
#         self.write("disable %s;" % self.labelStack[-1])


    def visit_Continue(self, node):
        self.write("disable %s;" % self.labelStack[-1])



#     def visitDiscard(self, node, *args):
#         expr = node.expr
#         # skip extra semicolons and wrongly-placed docstrings
#         if isinstance(expr, astNode.Const):
#             return
#         self.visit(expr)
#         # ugly hack to detect an orphan "task" call
#         if isinstance(expr, astNode.CallFunc) and hasattr(expr, 'tree'):
#             self.write(';')

    def visit_Expr(self, node):
        expr = node.value
        # skip extra semicolons and wrongly-placed docstrings
        if isinstance(expr, (ast.Num, ast.Str)):
            return
        self.visit(expr)
        # ugly hack to detect an orphan "task" call
        if isinstance(expr, ast.Call) and hasattr(expr, 'tree'):
            self.write(';')



#     def visitFor(self, node, *args):
#         self.labelStack.append(node.breakLabel)
#         self.labelStack.append(node.loopLabel)
#         var = node.assign.name
#         cf = node.list
#         f = self.getObj(cf.node)
#         args = cf.args
#         assert len(args) <= 3
#         if f is range:
#             cmp = '<'
#             op = '+'
#             oneoff = ''
#             if len(args) == 1:
#                 start, stop, step = None, args[0], None
#             elif len(args) == 2:
#                 start, stop, step = args[0], args[1], None
#             else:
#                 start, stop, step = args
#         else: # downrange
#             cmp = '>='
#             op = '-'
#             oneoff ='-1'
#             if len(args) == 1:
#                 start, stop, step = args[0], None, None
#             elif len(args) == 2:
#                 start, stop, step = args[0], args[1], None
#             else:
#                 start, stop, step = args
#         if node.breakLabel.isActive:
#             self.write("begin: %s" % node.breakLabel)
#             self.writeline()
#         self.write("for (%s=" % var)
#         if start is None:
#             self.write("0")
#         else:
#             self.visit(start)
#         self.write("%s; %s%s" % (oneoff, var, cmp))
#         if stop is None:
#             self.write("0")
#         else:
#             self.visit(stop)
#         self.write("; %s=%s%s" % (var, var, op))
#         if step is None:
#             self.write("1")
#         else:
#             v = self.getVal(step)
#             self.require(node, v >= 0, "step should be >= 0")
#             self.visit(step)
#         self.write(") begin")
#         if node.loopLabel.isActive:
#             self.write(": %s" % node.loopLabel)
#         self.indent()
#         self.visit(node.body)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         if node.breakLabel.isActive:
#             self.writeline()
#             self.write("end")
#         self.labelStack.pop()
#         self.labelStack.pop()


    def visit_For(self, node):
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        var = node.target.id
        cf = node.iter
        f = self.getObj(cf.func)
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
            v = self.getVal(step)
            self.require(node, v >= 0, "step should be >= 0")
            self.visit(step)
        self.write(") begin")
        if node.loopLabel.isActive:
            self.write(": %s" % node.loopLabel)
        self.indent()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()



#     def visitFunction(self, node, *args):
#         raise AssertionError("To be implemented in subclass")

    def visit_FunctionDef(self, node):
        raise AssertionError("To be implemented in subclass")






#     def visitIf(self, node, *args):
#         if node.ignore:
#             return
#         if node.isCase:
#             self.mapToCase(node, *args)
#         else:
#             self.mapToIf(node, *args)

    def visit_If(self, node):
        if node.ignore:
            return
        if node.isCase:
            self.mapToCase(node)
        else:
            self.mapToIf(node)

    def mapToCase(self, node, *args):
        var = node.caseVar
#        self.write("// synthesis parallel_case")
#        if node.isFullCase:
#            self.write(" full_case")
#        self.writeline()
        self.write("casez (")
        self.visit(var)
        self.write(")")
        self.indent()
        for test, suite in node.tests:
            self.writeline()
            item = test.comparators[0].obj
            self.write(item._toVerilog(dontcare=True))
            self.write(": begin")
            self.indent()
            self.visit_stmt(suite)
            self.dedent()
            self.writeline()
            self.write("end")
        if node.else_:
            self.writeline()
            self.write("default: begin")
            self.indent()
            self.visit_stmt(node.else_)
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
            self.visit_stmt(suite)
            self.dedent()
            self.writeline()
            self.write("end")
        if node.else_:
            self.writeline()
            self.write("else begin")
            self.indent()
            self.visit_stmt(node.else_)
            self.dedent()
            self.writeline()
            self.write("end")





    def visitKeyword(self, node, *args):
        self.visit(node.expr)



    def visit_Module(self, node, *args):
        for stmt in node.body:
            self.visit(stmt)
       

#     def visitAssName(self, node, *args):
#         self.write(node.name)




#     def visitName(self, node, context=None, *args):
#         addSignBit = False
#         isMixedExpr = (not node.signed) and (context == _context.SIGNED)
#         n = node.name
#         if n == 'False':
#             s = "1'b0"
#         elif n == 'True':
#             s = "1'b1"
#         elif n in self.tree.vardict:
#             addSignBit = isMixedExpr
#             s = n
#         elif n in self.tree.argnames:
#             assert n in self.tree.symdict
#             addSignBit = isMixedExpr
#             s = n
#         elif n in self.tree.symdict:
#             obj = self.tree.symdict[n]
#             if isinstance(obj, bool):
#                 s = "%s" % int(obj)
#             elif isinstance(obj, (int, long)):
#                 self.writeIntSize(obj)
#                 s = str(obj)
#             elif isinstance(obj, Signal):
#                 addSignBit = isMixedExpr
#                 s = str(obj)
#             elif _isMem(obj):
#                 m = _getMemInfo(obj)
#                 assert m.name
#                 s = m.name
#             elif isinstance(obj, EnumItemType):
#                 s = obj._toVerilog()
#             elif type(obj) in (ClassType, TypeType) and issubclass(obj, Exception):
#                 s = n
#             else:
#                 self.raiseError(node, _error.UnsupportedType, "%s, %s" % (n, type(obj)))
#         else:
#             raise AssertionError("name ref: %s" % n)
#         if addSignBit:
#             self.write("$signed({1'b0, ")
#         self.write(s)
#         if addSignBit:
#             self.write("})")       


    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setName(node)
        else:
            self.getName(node)

    def setName(self, node):
        self.write(node.id)

    def getName(self, node):
        addSignBit = False
        isMixedExpr = (not node.signed) and (self.context == _context.SIGNED)
        n = node.id
        if n == 'False':
            s = "1'b0"
        elif n == 'True':
            s = "1'b1"
        elif n == 'None':
            s = "'bz"
        elif n in self.tree.vardict:
            addSignBit = isMixedExpr
            s = n
        elif n in self.tree.argnames:
            assert n in self.tree.symdict
            addSignBit = isMixedExpr
            s = n
        elif n in self.tree.symdict:
            obj = self.tree.symdict[n]
            if isinstance(obj, bool):
                s = "%s" % int(obj)
            elif isinstance(obj, (int, long)):
                s = self.IntRepr(obj)
            elif isinstance(obj, _Signal):
                addSignBit = isMixedExpr
                s = str(obj)
            elif _isMem(obj):
                m = _getMemInfo(obj)
                assert m.name
                s = m.name
            elif isinstance(obj, EnumItemType):
                s = obj._toVerilog()
            elif type(obj) in (ClassType, TypeType) and issubclass(obj, Exception):
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



#     def visitPass(self, node, *args):
#         self.write("// pass")

    def visit_Pass(self, node):
        self.write("// pass")



##     def handlePrint(self, node):
##         self.write('$display(')
##         s = node.nodes[0]
##         self.visit(s, _context.PRINT)
##         for s in node.nodes[1:]:
##             self.write(', , ')
##             self.visit(s, _context.PRINT)
##         self.write(');')
    
##     def visitPrint(self, node, *args):
##         self.handlePrint(node)

#     def visitPrintnl(self, node, *args):
#         argnr = 0
#         for s in node.format:
#             if isinstance(s, str):
#                 self.write('$write("%s");' % s)
#             else:
#                 a = node.args[argnr]
#                 argnr += 1
#                 obj = a.obj
#                 fs = "%0d"
#                 if isinstance(obj, str):
#                     self.write('$write(')
#                     self.visit(a, _context.PRINT)
#                     self.write(');')
#                 elif (s.conv is str) and isinstance(obj, bool):
#                     self.write('if (')
#                     self.visit(a, _context.PRINT)
#                     self.write(')')
#                     self.writeline()
#                     self.write('    $write("True");')
#                     self.writeline()
#                     self.write('else')
#                     self.writeline()
#                     self.write('    $write("False");')
#                 elif isinstance(obj, EnumItemType):
#                     tipe = obj._type
#                     self.write('case (')
#                     self.visit(a, _context.PRINT)
#                     self.write(')')
#                     self.indent()
#                     for n in tipe._names:
#                         self.writeline()
#                         item = getattr(tipe, n)
#                         self.write("'b%s: " % item._val)
#                         self.write('$write("%s");' % n)
#                     self.dedent()
#                     self.writeline()
#                     self.write("endcase")
#                 else:
#                     self.write('$write("%s", ' % fs)
#                     self.visit(a, _context.PRINT)
#                     self.write(');')
#             self.writeline()
#         self.write('$write("\\n");')

    def visit_Print(self, node):
        argnr = 0
        for s in node.format:
            if isinstance(s, str):
                self.write('$write("%s");' % s)
            else:
                a = node.args[argnr]
                argnr += 1
                obj = a.obj
                fs = "%0d"
                self.context =_context.PRINT
                if isinstance(obj, str):
                    self.write('$write(')
                    self.visit(a)
                    self.write(');')
                elif (s.conv is str) and isinstance(obj, bool):
                    self.write('if (')
                    self.visit(a)
                    self.write(')')
                    self.writeline()
                    self.write('    $write("True");')
                    self.writeline()
                    self.write('else')
                    self.writeline()
                    self.write('    $write("False");')
                elif isinstance(obj, EnumItemType):
                    tipe = obj._type
                    self.write('case (')
                    self.visit(a)
                    self.write(')')
                    self.indent()
                    for n in tipe._names:
                        self.writeline()
                        item = getattr(tipe, n)
                        self.write("'b%s: " % item._val)
                        self.write('$write("%s");' % n)
                    self.dedent()
                    self.writeline()
                    self.write("endcase")
                else:
                    self.write('$write("%s", ' % fs)
                    self.visit(a)
                    self.write(');')
                self.context = _context.UNKNOWN
            self.writeline()
        self.write('$write("\\n");')
        
    
#     def visitRaise(self, node, *args):
# ##         self.write('$display("')
# ##         self.visit(node.expr1)
# ##         self.write('");')
# ##         self.writeline()
#         self.write("$finish;")


    def visit_Raise(self, node):
        self.write("$finish;")

        
#     def visitReturn(self, node, *args):
#         self.write("disable %s;" % self.returnLabel)

    def visit_Return(self, node):
        self.write("disable %s;" % self.returnLabel)



#     def visitSlice(self, node, context=None, *args):
#         if isinstance(node.expr, astNode.CallFunc) and \
#            node.expr.node.obj is intbv and \
#            _isConstant(node.expr.args[0], self.tree.symdict):
#             c = self.getVal(node)
#             self.write("%s'h" % c._nrbits)
#             self.write("%x" % c._val)
#             return
#         addSignBit = (node.flags == 'OP_APPLY') and (context == _context.SIGNED)
#         if addSignBit:
#             self.write("$signed({1'b0, ")
#         self.visit(node.expr)
#         # special shortcut case for [:] slice
#         if node.lower is None and node.upper is None:
#             return
#         self.write("[")
#         if node.lower is None:
#             self.write("%s" % node.obj._nrbits)
#         else:
#             self.visit(node.lower)
#         self.write("-1:")
#         if node.upper is None:
#             self.write("0")
#         else:
#             self.visit(node.upper)
#         self.write("]")
#         if addSignBit:
#             self.write("})")


#     def visitSubscript(self, node, context=None, *args):
#         addSignBit = (node.flags == 'OP_APPLY') and \
#                      (not node.signed) and \
#                      (context == _context.SIGNED)
#         if addSignBit:
#             self.write("$signed({1'b0, ")
#         self.visit(node.expr)
#         self.write("[")
#         assert len(node.subs) == 1
#         self.visit(node.subs[0])
#         self.write("]")
#         if addSignBit:
#             self.write("})")

    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)

    def accessSlice(self, node):
        if isinstance(node.value, ast.Call) and \
           node.value.func.obj is intbv and \
           _isConstant(node.value.args[0], self.tree.symdict):
            c = self.getVal(node)
            self.write("%s'h" % c._nrbits)
            self.write("%x" % c._val)
            return
        addSignBit = isinstance(node.ctx, ast.Load) and (self.context == _context.SIGNED)
        if addSignBit:
            self.write("$signed({1'b0, ")
        self.context = None
        self.visit(node.value)
        lower, upper = node.slice.lower, node.slice.upper
        # special shortcut case for [:] slice
        if lower is None and upper is None:
            return
        self.write("[")
        if lower is None:
            self.write("%s" % node.obj._nrbits)
        else:
            self.visit(lower)
        self.write("-1:")
        if upper is None:
            self.write("0")
        else:
            self.visit(upper)
        self.write("]")
        if addSignBit:
            self.write("})")


    def accessIndex(self, node):
        addSignBit = isinstance(node.ctx, ast.Load) and \
                     (not node.signed) and \
                     (self.context == _context.SIGNED)
        if addSignBit:
            self.write("$signed({1'b0, ")
        self.context = None
        self.visit(node.value)
        self.write("[")
        # assert len(node.subs) == 1
        self.visit(node.slice.value)
        self.write("]")
        if addSignBit:
            self.write("})")


#     def visitStmt(self, node, *args):
#         for stmt in node.nodes:
#             self.writeline()
#             self.visit(stmt)
#             # ugly hack to detect an orphan "task" call
#             if isinstance(stmt, astNode.CallFunc) and hasattr(stmt, 'tree'):
#                 self.write(';')

    def visit_stmt(self, body):
        for stmt in body:
            if isinstance(stmt, ast.Expr):
                continue # skip docstrings
            self.writeline()
            self.visit(stmt)
            # ugly hack to detect an orphan "task" call
            if isinstance(stmt, ast.Call) and hasattr(stmt, 'tree'):
                self.write(';')


#     def visitTuple(self, node, context=None, *args):
#         assert context != None
#         sep = ", "
#         tpl = node.nodes
#         self.visit(tpl[0])
#         for elt in tpl[1:]:
#             self.write(sep)
#             self.visit(elt)


    def visit_Tuple(self, node):
        assert self.context != None
        sep = ", "
        tpl = node.elts
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(sep)
            self.visit(elt)


#     def visitWhile(self, node, *args):
#         self.labelStack.append(node.breakLabel)
#         self.labelStack.append(node.loopLabel)
#         if node.breakLabel.isActive:
#             self.write("begin: %s" % node.breakLabel)
#             self.writeline()
#         self.write("while (")
#         self.visit(node.test)
#         self.write(") begin")
#         if node.loopLabel.isActive:
#             self.write(": %s" % node.loopLabel)
#         self.indent()
#         self.visit(node.body)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         if node.breakLabel.isActive:
#             self.writeline()
#             self.write("end")
#         self.labelStack.pop()
#         self.labelStack.pop()


    def visit_While(self, node):
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
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()



        
#     def visitYield(self, node, *args):
#         yieldObj = self.getObj(node.value)
#         assert node.senslist
#         senslist = node.senslist
#         if isinstance(yieldObj, delay):
#             self.write("# ")
#             self.visit(node.value, _context.YIELD)
#             self.write(";")
#         else:
#             self.writeSensitivityList(senslist)
#             self.write(";")

    def visit_Yield(self, node):
        yieldObj = self.getObj(node.value)
        assert node.senslist
        senslist = node.senslist
        if isinstance(yieldObj, delay):
            self.write("# ")
            self.context = _context.YIELD
            self.visit(node.value)
            self.context = _context.UNKNOWN
            self.write(";")
        else:
            self.writeSensitivityList(senslist)
            self.write(";")





        
class _ConvertAlwaysVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         w = node.code.nodes[-1]
#         y = w.body.nodes[0]
#         if isinstance(y, astNode.Discard):
#             y = y.expr
#         assert isinstance(y, astNode.Yield)
#         self.writeAlwaysHeader()
#         self.writeDeclarations()
#         assert isinstance(w.body, astNode.Stmt)
#         for stmt in w.body.nodes[1:]:
#             self.writeline()
#             self.visit(stmt)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        w = node.body[-1]
        y = w.body[0]
        if isinstance(y, ast.Expr):
            y = y.value
        assert isinstance(y, ast.Yield)
        self.writeAlwaysHeader()
        self.writeDeclarations()
        # assert isinstance(w.body, astNode.Stmt)
        for stmt in w.body[1:]:
            self.writeline()
            self.visit(stmt)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)


class _ConvertInitialVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         self.write("initial begin: %s" % self.tree.name) 
#         self.indent()
#         self.writeDeclarations()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        self.write("initial begin: %s" % self.tree.name) 
        self.indent()
        self.writeDeclarations()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)




class _ConvertAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        if toVerilog.prefer_blocking_assignments:
            self.okSigAss = False
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         self.writeAlwaysHeader()
#         self.writeDeclarations()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.writeAlwaysHeader()
        self.writeDeclarations()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)



        
class _ConvertSimpleAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitAssAttr(self, node, *args):
#         self.write("assign ")
#         self.visit(node.expr)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.write("assign ")
            self.visit(node.value)
        else:
            self.generic_visit(node)

#     def visitFunction(self, node, *args):
#         self.visit(node.code)
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.visit_stmt(node.body)
        self.writeline(2)





        
class _ConvertAlwaysDecoVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         self.writeAlwaysHeader()
#         self.writeDeclarations()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.writeAlwaysHeader()
        self.writeDeclarations()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)


       
    
class _ConvertFunctionVisitor(_ConvertVisitor):
    
    def __init__(self, tree, funcBuf):
        _ConvertVisitor.__init__(self, tree, funcBuf)
        self.returnObj = tree.returnObj
        self.returnLabel = _Label("RETURN")

    def writeOutputDeclaration(self):
        obj = self.tree.returnObj
        self.writeDeclaration(obj, self.tree.name, dir='')

    def writeInputDeclarations(self):
        for name in self.tree.argnames:
            obj = self.tree.symdict[name]
            self.writeline()
            self.writeDeclaration(obj, name, "input")
            
#     def visitFunction(self, node, *args):
#         self.write("function ")
#         self.writeOutputDeclaration()
#         self.indent()
#         self.writeInputDeclarations()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin: %s" % self.returnLabel)
#         self.indent()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline()
#         self.write("endfunction")
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.write("function ")
        self.writeOutputDeclaration()
        self.indent()
        self.writeInputDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endfunction")
        self.writeline(2)



#     def visitReturn(self, node, *args):
#         self.write("%s = " % self.tree.name)
#         self.visit(node.value)
#         self.write(";")
#         self.writeline()
#         self.write("disable %s;" % self.returnLabel)


    def visit_Return(self, node):
        self.write("%s = " % self.tree.name)
        self.visit(node.value)
        self.write(";")
        self.writeline()
        self.write("disable %s;" % self.returnLabel)


    
    
class _ConvertTaskVisitor(_ConvertVisitor):
    
    def __init__(self, tree, funcBuf):
        _ConvertVisitor.__init__(self, tree, funcBuf)
        self.returnLabel = _Label("RETURN")

    def writeInterfaceDeclarations(self):
        for name in self.tree.argnames:
            obj = self.tree.symdict[name]
            output = name in self.tree.outputs
            input = name in self.tree.inputs
            inout = input and output
            dir = (inout and "inout") or (output and "output") or "input"
            self.writeline()
            self.writeDeclaration(obj, name, dir)
            
#     def visitFunction(self, node, *args):
#         self.write("task %s;" % self.tree.name)
#         self.indent()
#         self.writeInterfaceDeclarations()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin: %s" % self.returnLabel)
#         self.indent()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end")
#         self.writeline()
#         self.write("endtask")
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.write("task %s;" % self.tree.name)
        self.indent()
        self.writeInterfaceDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endtask")
        self.writeline(2)
