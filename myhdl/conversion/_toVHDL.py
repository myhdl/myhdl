#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2009 Jan Decaluwe
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

""" myhdl toVHDL conversion module.

"""


import sys
import os
import math

import inspect
from datetime import datetime
#import compiler
#from compiler import ast as astNode
import ast
from types import GeneratorType, FunctionType, ClassType, StringType
from cStringIO import StringIO
import __builtin__
import warnings
from copy import copy
import string

import myhdl
from myhdl import *
from myhdl import ToVHDLError, ToVHDLWarning
from myhdl._extractHierarchy import (_HierExtr, _isMem, _getMemInfo,
                                     _UserVhdlCode, _userCodeMap)

from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl._instance import _Instantiator
from myhdl.conversion._misc import (_error, _access, _kind,_context,
                                    _ConversionMixin, _Label, _genUniqueSuffix, _isConstant)
from myhdl.conversion._analyze import (_analyzeSigs, _analyzeGens, _analyzeTopFunc,
                                       _Ram, _Rom, _enumTypeSet)
from myhdl._Signal import _Signal,_WaiterList
from myhdl.conversion._toVHDLPackage import _package

_version = myhdl.__version__.replace('.','')
_converting = 0
_profileFunc = None
_enumTypeList = []

def _checkArgs(arglist):
    for arg in arglist:
        if not isinstance(arg, (GeneratorType, _Instantiator, _UserVhdlCode)):
            raise ToVHDLError(_error.ArgType, arg)
        
def _flatten(*args):
    arglist = []
    for arg in args:
        if id(arg) in _userCodeMap['vhdl']:
            arglist.append(_userCodeMap['vhdl'][id(arg)])
        elif isinstance(arg, (list, tuple, set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist
        
def _makeDoc(doc, indent=''):
    if doc is None:
        return ''
    doc = inspect.cleandoc(doc)
    pre = '\n' + indent + '-- '
    doc = '-- ' + doc
    doc = doc.replace('\n', pre)
    return doc




class _ToVHDLConvertor(object):

    __slots__ = ("name",
                 "component_declarations",
                 "header",
                 "no_myhdl_header"
                 )

    def __init__(self):
        self.name = None
        self.component_declarations = None
        self.header = ''
        self.no_myhdl_header = False

    def __call__(self, func, *args, **kwargs):
        global _converting
        if _converting:
            return func(*args, **kwargs) # skip
        else:
            # clean start
            sys.setprofile(None)
        from myhdl import _traceSignals
        if _traceSignals._tracing:
            raise ToVHDLError("Cannot use toVHDL while tracing signals")
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

        compDecls = self.component_declarations

        vpath = name + ".vhd"
        vfile = open(vpath, 'w')
        ppath = "pck_myhdl_%s.vhd" % _version
        pfile = None
        if not os.path.isfile(ppath):
            pfile = open(ppath, 'w')

        ### initialize properly ###
        _genUniqueSuffix.reset()
        _enumTypeSet.clear()

        siglist, memlist = _analyzeSigs(h.hierarchy, hdl='VHDL')
        arglist = _flatten(h.top)
        # print h.top
        _checkArgs(arglist)
        genlist = _analyzeGens(arglist, h.absnames)
        _annotateTypes(genlist)
        intf = _analyzeTopFunc(func, *args, **kwargs)
        intf.name = name
        doc = _makeDoc(inspect.getdoc(func))
        
        needPck = len(_enumTypeSet) > 0
        
        if pfile:
            _writeFileHeader(pfile, ppath)
            print >> pfile, _package
            pfile.close()

        _writeFileHeader(vfile, vpath)
        if needPck:
            _writeCustomPackage(vfile, intf)
        _writeModuleHeader(vfile, intf, needPck, doc)
        _writeFuncDecls(vfile)
        _writeSigDecls(vfile, intf, siglist, memlist)
        _writeCompDecls(vfile, compDecls)
        _convertGens(genlist, siglist, vfile)
        _writeModuleFooter(vfile)

        vfile.close()
        # tbfile.close()

        ### clean-up properly ###
        
        # clean up signal names
        for sig in siglist:
            sig._clear()
#             sig._name = None
#             sig._driven = False
#             sig._read = False
            
        # clean up attributes
        self.name = None
        self.component_declarations = None
        self.header = ''
        self.no_myhdl_header = False

        return h.top
    

toVHDL = _ToVHDLConvertor()

myhdl_header = """\
-- File: $filename
-- Generated by MyHDL $version
-- Date: $date
"""

def _writeFileHeader(f, fn):
    vars = dict(filename=fn, 
                version=myhdl.__version__,
                date=datetime.today().ctime()
                )
    if not toVHDL.no_myhdl_header:
        print >> f, string.Template(myhdl_header).substitute(vars)
    if toVHDL.header:
        print >> f, string.Template(toVHDL.header).substitute(vars)
    print >> f



def _writeCustomPackage(f, intf):
    print >> f
    print >> f, "package pck_%s is" % intf.name
    print >> f
    _sortedEnumTypeList = list(_enumTypeSet)
    _sortedEnumTypeList.sort(cmp=lambda a, b: cmp(a._name, b._name))
    for t in _sortedEnumTypeList:
        print >> f, "    %s" % t._toVHDL()
    print >> f
    print >> f, "end package pck_%s;" % intf.name
    print >> f


def _writeModuleHeader(f, intf, needPck, doc):
    print >> f, "library IEEE;"
    print >> f, "use IEEE.std_logic_1164.all;"
    print >> f, "use IEEE.numeric_std.all;"
    print >> f, "use std.textio.all;"
    print >> f
    print >> f, "use work.pck_myhdl_%s.all;" % _version
    print >> f
    if needPck:
        print >> f, "use work.pck_%s.all;" % intf.name
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
            if s._inList:
                raise ToVHDLError(_error.PortInList, portname)
            # make sure signal name is equal to its port name
            s._name = portname
            r = _getRangeString(s)
            p = _getTypeString(s)
            if s._driven:
                if s._read:
                    warnings.warn("%s: %s" % (_error.OutputPortRead, portname),
                                  category=ToVHDLWarning
                                  )
                    f.write("\n        %s: inout %s%s" % (portname, p, r))
                else:
                    f.write("\n        %s: out %s%s" % (portname, p, r))
            else:
                if not s._read:
                    warnings.warn("%s: %s" % (_error.UnusedPort, portname),
                                  category=ToVHDLWarning
                                  )
                f.write("\n        %s: in %s%s" % (portname, p, r))
        f.write("\n    );\n")
    print >> f, "end entity %s;" % intf.name
    print >> f, doc
    print >> f
    print >> f, "architecture MyHDL of %s is" % intf.name
    print >> f



def _writeFuncDecls(f):
    return
    # print >> f, package


constwires = []


def _writeSigDecls(f, intf, siglist, memlist):
    del constwires[:]
    for s in siglist:
        if not s._used:
            continue
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        p = _getTypeString(s)
        if s._driven:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnreadSignal, s._name),
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
        if not m._used:
            continue
        r = _getRangeString(m.elObj)
        p = _getTypeString(m.elObj)
        t = "t_array_%s" % m.name
        print >> f, "type %s is array(0 to %s-1) of %s%s;" % (t, m.depth, p, r)
        print >> f, "signal %s: %s;" % (m.name, t)
    print >> f

def _writeCompDecls(f,  compDecls):
    if compDecls is not None:
        print >> f, compDecls

def _writeModuleFooter(f):
    print >> f, "end architecture MyHDL;"

    

    
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


def _convertGens(genlist, siglist, vfile):
    blockBuf = StringIO()
    funcBuf = StringIO()
    for tree in genlist:
        if isinstance(tree, _UserVhdlCode):
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
    # shadow signal assignments
    for s in siglist:
        if hasattr(s, 'toVHDL') and s._read:
            print >> vfile, s.toVHDL()
    print >> vfile

    vfile.write(blockBuf.getvalue()); blockBuf.close()


opmap = {
    ast.Add      : '+',
    ast.Sub      : '-',
    ast.Mult     : '*',
    ast.Div      : '/',
    ast.Mod      : 'mod',
    ast.Pow      : '**',
    ast.LShift   : 'shift_left',
    ast.RShift   : 'shift_right',
    ast.BitOr    : 'or',
    ast.BitAnd   : 'and',
    ast.BitXor   : 'xor',
    ast.FloorDiv : '/',
    ast.Invert   : 'not ',
    ast.Not      : 'not ',
    ast.UAdd     : '+',
    ast.USub     : '-',
    ast.Eq       : '=',
    ast.Gt       : '>',
    ast.GtE      : '>=',
    ast.Lt       : '<',
    ast.LtE      : '<=',
    ast.NotEq    : '/=',
    ast.And      : 'and',
    ast.Or       : 'or',
}
    

class _ConvertVisitor(ast.NodeVisitor, _ConversionMixin):
    
    def __init__(self, tree, buf):
        self.tree = tree
        self.buf = buf
        self.returnLabel = tree.name
        self.ind = ''
        self.isSigAss = False
        self.labelStack = []
        self.context = None
 
        
    def write(self, arg):
        self.buf.write("%s" % arg)

    def writeline(self, nr=1):
        for i in range(nr):
            self.buf.write("\n%s" % self.ind)
            
    def writeDoc(self, node):
        assert hasattr(node, 'doc')
        doc = _makeDoc(node.doc, self.ind)
        self.write(doc)
        self.writeline() 
            
    def IntRepr(self, obj):     
        if obj >= 0:
            s = "%s" % int(obj)
        else:
            s = "(- %s)" % abs(int(obj))
        return s
    
    def BitRepr(self, item, var):
        return '"%s"' % bin(item, len(var))
        

    def inferCast(self, vhd, ori):
        pre, suf = "", ""
        if isinstance(vhd, vhd_int):
            if not isinstance(ori, vhd_int):
                pre, suf = "to_integer(", ")"
        elif isinstance(vhd, vhd_unsigned):
            if isinstance(ori, vhd_unsigned):
                if vhd.size != ori.size:
                    pre, suf = "resize(", ", %s)" % vhd.size
            elif isinstance(ori, vhd_signed):
                if vhd.size != ori.size:
                    # note the order of resizing and casting here (otherwise bug!)
                    pre, suf = "resize(unsigned(", "), %s)" % vhd.size
                else:
                    pre, suf = "unsigned(", ")"
            else:
                pre, suf = "to_unsigned(", ", %s)" % vhd.size
        elif isinstance(vhd, vhd_signed):
            if isinstance(ori, vhd_signed):
                if vhd.size != ori.size:
                    pre, suf = "resize(", ", %s)" % vhd.size
            elif isinstance(ori, vhd_unsigned):
                if vhd.size != ori.size:
                    # I think this should be the order of resizing and casting here
                    pre, suf = "signed(resize(", ", %s))" % vhd.size
                else:
                    pre, suf = "signed(", ")"
            else:
                pre, suf = "to_signed(", ", %s)" % vhd.size
        elif isinstance(vhd, vhd_boolean):
            if not isinstance(ori, vhd_boolean):
                pre, suf = "to_boolean(", ")"
        elif isinstance(vhd, vhd_std_logic):
            if not isinstance(ori, vhd_std_logic):
                pre, suf = "to_std_logic(", ")"     
        elif isinstance(vhd, vhd_string):
            if isinstance(ori, vhd_enum):
                pre, suf = "%s'image(" % ori._type._name, ")"
                
        return pre, suf

                    
    def writeIntSize(self, n):
        # write size for large integers (beyond 32 bits signed)
        # with some safety margin
        if n >= 2**30:
            size = int(math.ceil(math.log(n+1,2))) + 1  # sign bit!
            self.write("%s'sd" % size)

    def writeDeclaration(self, obj, name, kind="", dir="", endchar=";", constr=True):
        if isinstance(obj, EnumItemType):
            tipe = obj._type._name
        elif isinstance(obj, _Ram):
            tipe = "t_array_%s" % name
            elt = inferVhdlObj(obj.elObj).toStr(True)
            self.write("type %s is array(0 to %s-1) of %s;" % (tipe, obj.depth, elt))
            self.writeline()
        else:
            vhd = inferVhdlObj(obj)
            if isinstance(vhd, vhd_enum):
                tipe = obj._val._type._name
            else:
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
        if self.tree.hasPrint:
            self.writeline()
            self.write("variable L: line;")
        for name, obj in self.tree.vardict.items():
            if isinstance(obj, _loopInt):
                continue # hack for loop vars
            self.writeline()
            self.writeDeclaration(obj, name, kind="variable")
                
    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]


    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            self.shiftOp(node)
        elif isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)):
            self.BitOp(node)
        elif isinstance(node.op, ast.Mod) and (self.context == _context.PRINT):
            self.visit(node.left)
            self.write(", ")
            self.visit(node.right)
        else:
            self.BinOp(node)
        
        
#     def binaryOp(self, node, op=None):
#         pre, suf = self.inferBinaryOpCast(node, node.left, node.right, op)
#         self.write(pre)
#         self.visit(node.left)
#         self.write(" %s " % op)
#         self.visit(node.right)
#         self.write(suf)
        
        
    def inferBinaryOpCast(self, node, left, right, op):
        ns, os = node.vhd.size, node.vhdOri.size
        ds = ns - os
        if ds > 0:
            if isinstance(left.vhd, vhd_vector) and isinstance(right.vhd, vhd_vector):
                if isinstance(op, (ast.Add, ast.Sub)):
                    left.vhd.size = ns
                    node.vhdOri.size = ns
                elif isinstance(op, ast.Mod):
                    right.vhd.size = ns
                    node.vhdOri.size = ns
                elif isinstance(op, ast.FloorDiv):
                    left.vhd.size = ns
                    node.vhdOri.size = ns
                elif isinstance(op, ast.Mult):
                    left.vhd.size += ds
                    node.vhdOri.size = ns
                else:
                    raise AssertionError("unexpected op %s" % op)
            elif isinstance(left.vhd, vhd_vector) and isinstance(right.vhd, vhd_int):
                if isinstance(op, (ast.Add, ast.Sub, ast.Mod, ast.FloorDiv)):
                    left.vhd.size = ns
                    node.vhdOri.size = ns
                elif isinstance(op, ast.Mult): 
                    left.vhd.size += ds
                    node.vhdOri.size = 2 * left.vhd.size
                else:
                    raise AssertionError("unexpected op %s" % op)
            elif isinstance(left.vhd, vhd_int) and isinstance(right.vhd, vhd_vector):
                if isinstance(op, ast.Add, ast.Sub, ast.Mod, ast.FloorDiv):
                    right.vhd.size = ns
                    node.vhdOri.size = ns
                elif isinstance(op, ast.Mult):
                    node.vhdOri.size = 2 * right.vhd.size                  
                else:
                    raise AssertionError("unexpected op %s" % op)
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        if pre == "":
            pre, suf = "(", ")"
        return pre, suf
        
 
#     def visitAdd(self, node, *args):
#         self.binaryOp(node, '+')
#     def visitFloorDiv(self, node, *args):
#         self.binaryOp(node, '/')
#     def visitMod(self, node, context=None, *args):
#         if context == _context.PRINT:
#             self.visit(node.left, _context.PRINT)
#             self.write(", ")
#             self.visit(node.right, _context.PRINT)
#         else:
#             self.binaryOp(node, 'mod')        
#     def visitMul(self, node, *args):
#         self.binaryOp(node, '*')
#     def visitPower(self, node, *args):
#          self.binaryOp(node, '**')
#     def visitSub(self, node, *args):
#         self.binaryOp(node, "-")

    def BinOp(self, node):
        pre, suf = self.inferBinaryOpCast(node, node.left, node.right, node.op)
        self.write(pre)
        self.visit(node.left)
        self.write(" %s " % opmap[type(node.op)])
        self.visit(node.right)
        self.write(suf)
  


#     def shiftOp(self, node, op=None):
#         pre, suf = self.inferShiftOpCast(node, node.left, node.right, op)
#         self.write(pre)
#         self.write("%s(" % op)
#         self.visit(node.left)
#         self.write(", ")
#         self.visit(node.right)
#         self.write(")")
#         self.write(suf)

    def inferShiftOpCast(self, node, left, right, op):
        ns, os = node.vhd.size, node.vhdOri.size
        ds = ns - os
        if ds > 0:
            if isinstance(node.left.vhd, vhd_vector):
                left.vhd.size = ns
                node.vhdOri.size = ns
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        return pre, suf
               
#     def visitLeftShift(self, node, *args):
#         self.shiftOp(node, "shift_left")
#     def visitRightShift(self, node, *args):
#         self.shiftOp(node, "shift_right")

    def shiftOp(self, node):
        pre, suf = self.inferShiftOpCast(node, node.left, node.right, node.op)
        self.write(pre)
        self.write("%s(" % opmap[type(node.op)])
        self.visit(node.left)
        self.write(", ")
        self.visit(node.right)
        self.write(")")
        self.write(suf)
        

#     def checkOpWithNegIntbv(self, node, op):
#         if op in ("+", "-", "not ", "*", "&&", "||", "!"):
#             return
#         if isinstance(node, astNode.Name):
#             o = node.obj
#             if isinstance(o, (_Signal, intbv)) and o.min is not None and o.min < 0:
#                 self.raiseError(node, _error.NotSupported,
#                                 "negative intbv with operator %s" % op)

#     def multiBitOp(self, node, op):
#         for n in node.nodes:
#             self.checkOpWithNegIntbv(n, op)
#         self.write("(")
#         self.visit(node.nodes[0])
#         for n in node.nodes[1:]:
#             self.write(" %s " % op)
#             self.visit(n)
#         self.write(")")
#     def visitBitand(self, node, *args):
#         self.multiBitOp(node, 'and')
#     def visitBitor(self, node, *args):
#         self.multiBitOp(node, 'or')
#     def visitBitxor(self, node, *args):
#         self.multiBitOp(node, 'xor')

    def BitOp(self, node):
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        self.write(pre)
        self.write("(")
        self.visit(node.left)
        self.write(" %s " % opmap[type(node.op)])
        self.visit(node.right)
        self.write(")")
        self.write(suf)
         
        
#     def multiBoolOp(self, node, op):
#         for n in node.nodes:
#             self.checkOpWithNegIntbv(n, op)
#         if isinstance(node.vhd, vhd_std_logic):
#             self.write("to_std_logic")
#         self.write("(")
#         self.visit(node.nodes[0])
#         for n in node.nodes[1:]:
#             self.write(" %s " % op)
#             self.visit(n)
#         self.write(")")
#     def visitAnd(self, node, *args):
#         self.multiBoolOp(node, 'and')
#     def visitOr(self, node, *args):
#         self.multiBoolOp(node, 'or')

    def visit_BoolOp(self, node):
        if isinstance(node.vhd, vhd_std_logic):
            self.write("to_std_logic")
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

#     def visitUnaryAdd(self, node, context=None, *args):
#         self.unaryOp(node, '+', context)
        
#     def visitUnarySub(self, node, context=None, *args):
#         pre, suf = self.inferCast(node.vhd, node.vhdOri)
#         self.write(pre)
#         self.write("(-")
#         self.visit(node.expr)
#         self.write(")")
#         self.write(suf)

#     def visitInvert(self, node, context=None, *args):
#         pre, suf = self.inferCast(node.vhd, node.vhdOri)
#         self.write(pre)
#         self.write("(not ")
#         self.visit(node.expr)
#         self.write(")")
#         self.write(suf)
       
#     def visitNot(self, node, context=None):
#         self.checkOpWithNegIntbv(node.expr, 'not ')
#         if isinstance(node.vhd, vhd_std_logic):
#             self.write("to_std_logic")
#         self.write("(not ")
#         self.visit(node.expr, context)
#         self.write(")")

    def visit_UnaryOp(self, node):
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        self.write(pre)
        self.write("(")
        self.write(opmap[type(node.op)])
        self.visit(node.operand)
        self.write(")")
        self.write(suf)
        


    
        


    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setAttr(node)
        else:
            self.getAttr(node)


#     def visitAssAttr(self, node, *args):
#         assert node.attrname == 'next'
#         self.isSigAss = True
#         self.visit(node.expr)
#         node.obj = self.getObj(node.expr)

    def setAttr(self, node):
        assert node.attr == 'next'
        self.isSigAss = True
        self.visit(node.value)
        node.obj = self.getObj(node.value)


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
#             elif node.attrname == 'posedge':
#                 self.write("rising_edge(")
#                 self.visit(node.expr)
#                 self.write(")")
#             elif node.attrname == 'negedge':
#                 self.write("falling_edge(")
#                 self.visit(node.expr)
#                 self.write(")")
#             elif node.attrname == 'val':
#                 pre, suf = self.inferCast(node.vhd, node.vhdOri)
#                 self.write(pre)
#                 self.visit(node.expr)
#                 self.write(suf)
#         if isinstance(obj, (Signal, intbv)):
#             if node.attrname in ('min', 'max'):
#                 self.write("%s" % node.obj)
#         if isinstance(obj, EnumType):
#             assert hasattr(obj, node.attrname)
#             e = getattr(obj, node.attrname)
#             self.write(e._toVHDL())

    def getAttr(self, node):
        assert isinstance(node.value, ast.Name), node.value
        n = node.value.id
        if n in self.tree.symdict:
            obj = self.tree.symdict[n]
        elif n in self.tree.vardict:
            obj = self.tree.vardict[n]
        else:
            raise AssertionError("object not found")
        if isinstance(obj, _Signal):
            if node.attr == 'next':
                self.isSigAss = True
                self.visit(node.value)
            elif node.attr == 'posedge':
                self.write("rising_edge(")
                self.visit(node.value)
                self.write(")")
            elif node.attr == 'negedge':
                self.write("falling_edge(")
                self.visit(node.value)
                self.write(")")
            elif node.attr == 'val':
                pre, suf = self.inferCast(node.vhd, node.vhdOri)
                self.write(pre)
                self.visit(node.value)
                self.write(suf)
        if isinstance(obj, (_Signal, intbv)):
            if node.attr in ('min', 'max'):
                self.write("%s" % node.obj)
        if isinstance(obj, EnumType):
            assert hasattr(obj, node.attr)
            e = getattr(obj, node.attr)
            self.write(e._toVHDL())





#     def visitAssert(self, node, *args):
#         # XXX
#         self.write("assert ")
#         self.visit(node.test)
#         self.indent()
#         self.writeline()
#         self.write('report "*** AssertionError ***"')
#         self.writeline()
#         self.write("severity error;")
#         self.dedent()


    def visit_Assert(self, node):
        # XXX
        self.write("assert ")
        self.visit(node.test)
        self.indent()
        self.writeline()
        self.write('report "*** AssertionError ***"')
        self.writeline()
        self.write("severity error;")
        self.dedent()




#     def visitAssign(self, node, *args):
#         assert len(node.nodes) == 1
#         lhs = node.nodes[0]
#         rhs = node.expr
#         # shortcut for expansion of ROM in case statement
#         if isinstance(node.expr, astNode.Subscript) and \
#                isinstance(node.expr.expr.obj, _Rom):
#             rom = node.expr.expr.obj.rom
#             self.write("case ")
#             self.visit(node.expr.subs[0])
#             self.write(" is")
#             self.indent()
#             size = lhs.vhd.size
#             for i, n in enumerate(rom):
#                 self.writeline()
#                 if i == len(rom)-1:
#                     self.write("when others => ")
#                 else:
#                     self.write("when %s => " % i)
#                 self.visit(lhs)
#                 if self.isSigAss:
#                     self.write(' <= ')
#                     self.isSigAss = False
#                 else:
#                     self.write(' := ')
#                 if isinstance(lhs.vhd, vhd_std_logic):
#                     self.write("'%s';" % n)
#                 elif isinstance(lhs.vhd, vhd_int):
#                     self.write("%s;" % n)
#                 else:
#                     self.write('"%s";' % bin(n, size))
#             self.dedent()
#             self.writeline()
#             self.write("end case;")
#             return
#         # default behavior
#         convOpen, convClose = "", ""
# ##         if isinstance(lhs.vhd, vhd_unsigned):
# ##             if isinstance(rhs.vhd, vhd_unsigned) and \
# ##                (lhs.vhd.size == rhs.vhd.size):
# ##                 pass
# ##             else:
# ##                 convOpen, convClose = "to_unsigned(", ", %s)" % lhs.vhd.size
# ##                 rhs.vhd = vhd_int()
# ##         elif isinstance(lhs.vhd, vhd_signed):
# ##             if isinstance(rhs.vhd, vhd_signed) and \
# ##                    (lhs.vhd.size == rhs.vhd.size):
# ##                 pass
# ##             else:
# ##                 convOpen, convClose = "to_signed(", ", %s)" % lhs.vhd.size
# ##                 rhs.vhd = vhd_int()
# ##         elif isinstance(lhs.vhd, vhd_std_logic):
# ##             rhs.vhd = vhd_std_logic()
#         if isinstance(lhs.vhd, vhd_type):
#             rhs.vhd = lhs.vhd
#         self.visit(node.nodes[0])
#         if self.isSigAss:
#             self.write(' <= ')
#             self.isSigAss = False
#         else:
#             self.write(' := ')
#         self.write(convOpen)
#         # node.expr.target = obj = self.getObj(node.nodes[0])
#         self.visit(node.expr)
#         self.write(convClose)
#         self.write(';')


    def visit_Assign(self, node):
        lhs = node.targets[0]
        rhs = node.value
        # shortcut for expansion of ROM in case statement
        if isinstance(node.value, ast.Subscript) and \
                isinstance(node.value.slice, ast.Index) and \
                isinstance(node.value.value.obj, _Rom):
            rom = node.value.value.obj.rom
            self.write("case ")
            self.visit(node.value.slice)
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
        if isinstance(lhs.vhd, vhd_type):
            rhs.vhd = lhs.vhd
        self.visit(lhs)
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' := ')
        self.write(convOpen)
        # node.expr.target = obj = self.getObj(node.nodes[0])
        self.visit(rhs)
        self.write(convClose)
        self.write(';')




#     def visitAugAssign(self, node, *args):
# ##         if node.op in ("|=", "&=", "^="):
# ##             self.bitOpAugAssign(node, *args)
# ##             return
#         opmap = {"+=" : "+",
#                  "-=" : "-",
#                  "*=" : "*",
#                  "//=" : "/",
#                  "%=" : "mod",
#                  "**=" : "**",
#                  "|=" : "or",
#                  ">>=" : "shift_right",
#                  "<<=" : "shift_left",
#                  "&=" : "and",
#                  "^=" : "xor"
#                  }
#         if node.op not in opmap:
#             self.raiseError(node, _error.NotSupported,
#                             "augmented assignment %s" % node.op)
#         op = opmap[node.op]
#         # XXX apparently no signed context required for augmented assigns
#         left, right, =  node.node, node.expr
#         isFunc = False
#         pre, suf = "", ""
#         if op in ('+', '-', '*', 'mod', '/'):
#             o = node.vhdOri
#             pre, suf = self.inferBinaryOpCast(node, left, right, op)
#         elif op in ("shift_left", "shift_right"):
#             isFunc = True
#             pre, suf = self.inferShiftOpCast(node, left, right, op)
#         self.visit(node.node)
#         self.write(" := ")
#         self.write(pre)
#         if isFunc:
#             self.write("%s(" % op)
#         self.visit(node.node)
#         if isFunc:
#             self.write(", ")
#         else:
#             self.write(" %s " % op)
#         self.visit(node.expr)
#         if isFunc:
#             self.write(")")
#         self.write(suf)
#         self.write(";")



    def visit_AugAssign(self, node):
        op = opmap[type(node.op)]
        # XXX apparently no signed context required for augmented assigns
        left, op, right =  node.target, node.op, node.value
        isFunc = False
        pre, suf = "", ""
        if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
            pre, suf = self.inferBinaryOpCast(node, left, right, op)
        elif isinstance(op, (ast.LShift, ast.RShift)):
            isFunc = True
            pre, suf = self.inferShiftOpCast(node, left, right, op)
        self.visit(left)
        self.write(" := ")
        self.write(pre)
        if isFunc:
            self.write("%s(" % opmap[type(op)])
        self.visit(left)
        if isFunc:
            self.write(", ")
        else:
            self.write(" %s " % opmap[type(op)])
        self.visit(right)
        if isFunc:
            self.write(")")
        self.write(suf)
        self.write(";")

     
         
#     def visitBreak(self, node, *args):
#         # self.write("disable %s;" % self.labelStack[-2])
#         self.write("exit;")

    def visit_Break(self, node):
        self.write("exit;")


#     def visitCallFunc(self, node, *args):
#         fn = node.node
#         # assert isinstance(fn, astNode.Name)
#         f = self.getObj(fn)
#         opening, closing = '(', ')'
#         sep = ", "
#         if f is bool:
#             opening, closing = '', ''
#             arg = node.args[0]
#             arg.vhd = node.vhd
# ##             self.write("(")
# ##             arg = node.args[0]
# ##             self.visit(arg)
# ##             if isinstance(arg, vhd_std_logic):
# ##                 test = "'0'"
# ##             else:
# ##                 test = "0"
# ##             self.write(" /= %s)" % test)
# ##             # self.write(" ? 1'b1 : 1'b0)")
# ##             return
#         elif f is len:
#             val = self.getVal(node)
#             self.require(node, val is not None, "cannot calculate len")
#             self.write(`val`)
#             return
#         elif f is now:
#             pre, suf = self.inferCast(node.vhd, node.vhdOri)
#             self.write(pre)
#             self.write("(now / 1 ns)")
#             self.write(suf)
#             return
#         elif f is ord:
#             opening, closing = '', ''
#             if isinstance(node.args[0], astNode.Const):
#                 if  type(node.args[0].value) != StringType:
#                     self.raiseError(node, _error.UnsupportedType, "%s" % (type(node.args[0].value)))
#                 elif len(node.args[0].value) > 1:
#                     self.raiseError(node, _error.UnsupportedType, "Strings with length > 1" )
#                 else:
#                     node.args[0].value = ord(node.args[0].value)
#         elif f in (int, long):
#             opening, closing = '', ''
#             # convert number argument to integer
#             if isinstance(node.args[0], astNode.Const):
#                 node.args[0].value = int(node.args[0].value)
#         elif f is intbv:
#             pre, post = "", ""
#             arg = node.args[0]
#             if isinstance(node.vhd, vhd_unsigned):
#                 pre, post = "to_unsigned(", ", %s)" % node.vhd.size
#             elif isinstance(node.vhd, vhd_signed):
#                 pre, post = "to_signed(", ", %s)" % node.vhd.size
#             self.write(pre)
#             self.visit(arg)
#             self.write(post)
#             return
#         elif f == intbv.signed: # note equality comparison
#             # this call comes from a getattr
#             arg = fn.expr
#             pre, suf = self.inferCast(node.vhd, node.vhdOri)
#             opening, closing = '', ''
#             if isinstance(arg.vhd, vhd_unsigned):
#                 opening, closing = "signed(", ")"
#             self.write(pre)
#             self.write(opening)
#             self.visit(arg)
#             self.write(closing)
#             self.write(suf)
#             return
#         elif type(f) is ClassType and issubclass(f, Exception):
#             self.write(f.__name__)
#         elif f in (posedge, negedge):
#             opening, closing = ' ', ''
#             self.write(f.__name__)
#         elif f is delay:
#             self.visit(node.args[0])
#             self.write(" ns")
#             return
#         elif f is concat:
#             opening, closing =  "unsigned'(", ")"
#             sep = " & "
#         elif hasattr(node, 'tree'):
#             self.write(node.tree.name)
#         else:
#             self.write(f.__name__)
#         if node.args:
#             self.write(opening)
#             self.visit(node.args[0], *args)
#             for arg in node.args[1:]:
#                 self.write(sep)
#                 self.visit(arg, *args)
#             self.write(closing)
#         if hasattr(node, 'tree'):
#             if node.tree.kind == _kind.TASK:
#                 Visitor = _ConvertTaskVisitor
#             else:
#                 Visitor = _ConvertFunctionVisitor
#             v = Visitor(node.tree, self.funcBuf)
#             compiler.walk(node.tree, v)

    def visit_Call(self, node):
        fn = node.func
        # assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        opening, closing = '(', ')'
        sep = ", "
        if f is bool:
            opening, closing = '', ''
            arg = node.args[0]
            arg.vhd = node.vhd
        elif f is len:
            val = self.getVal(node)
            self.require(node, val is not None, "cannot calculate len")
            self.write(`val`)
            return
        elif f is now:
            pre, suf = self.inferCast(node.vhd, node.vhdOri)
            self.write(pre)
            self.write("(now / 1 ns)")
            self.write(suf)
            return
        elif f is ord:
            opening, closing = '', ''
            if isinstance(node.args[0], ast.Str):
                if len(node.args[0].s) > 1:
                    self.raiseError(node, _error.UnsupportedType, "Strings with length > 1" )
                else:
                    node.args[0].s = ord(node.args[0].s)
        elif f in (int, long):
            opening, closing = '', ''
            # convert number argument to integer
            if isinstance(node.args[0], ast.Num):
                node.args[0].n = int(node.args[0].n)
        elif f is intbv:
            pre, post = "", ""
            arg = node.args[0]
            if isinstance(node.vhd, vhd_unsigned):
                pre, post = "to_unsigned(", ", %s)" % node.vhd.size
            elif isinstance(node.vhd, vhd_signed):
                pre, post = "to_signed(", ", %s)" % node.vhd.size
            self.write(pre)
            self.visit(arg)
            self.write(post)
            return
        elif f == intbv.signed: # note equality comparison
            # this call comes from a getattr
            arg = fn.value
            pre, suf = self.inferCast(node.vhd, node.vhdOri)
            opening, closing = '', ''
            if isinstance(arg.vhd, vhd_unsigned):
                opening, closing = "signed(", ")"
            self.write(pre)
            self.write(opening)
            self.visit(arg)
            self.write(closing)
            self.write(suf)
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
            opening, closing =  "unsigned'(", ")"
            sep = " & "
        elif hasattr(node, 'tree'):
            self.write(node.tree.name)
        else:
            self.write(f.__name__)
        if node.args:
            self.write(opening)
            self.visit(node.args[0])
            for arg in node.args[1:]:
                self.write(sep)
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
#         n = node.vhd
#         ns = node.vhd.size
#         pre, suf = "(", ")"
#         if isinstance(n, vhd_std_logic):
#             pre = "to_std_logic("
#         elif isinstance(n, vhd_unsigned):
#             pre, suf = "to_unsigned(", ", %s)" % ns
#         elif isinstance(n, vhd_signed):
#             pre, suf = "to_signed(", ", %s)" % ns
            
#         self.write(pre)
#         self.visit(node.expr)
#         op, code = node.ops[0]
#         if op == "==":
#             op = "="
#         elif op == "!=":
#             op = "/="
#         self.write(" %s " % op)
#         self.visit(code)
#         self.write(suf)


    def visit_Compare(self, node):
        n = node.vhd
        ns = node.vhd.size
        pre, suf = "(", ")"
        if isinstance(n, vhd_std_logic):
            pre = "to_std_logic("
        elif isinstance(n, vhd_unsigned):
            pre, suf = "to_unsigned(", ", %s)" % ns
        elif isinstance(n, vhd_signed):
            pre, suf = "to_signed(", ", %s)" % ns
        self.write(pre)
        self.visit(node.left)
        op, right = node.ops[0], node.comparators[0]
        self.write(" %s " % opmap[type(op)])
        self.visit(right)
        self.write(suf)


#     def visitConst(self, node, context=None, *args):
#         if context == _context.PRINT:
#             # self.write('"%s"' % node.value)
#             pass
#         if isinstance(node.vhd, vhd_std_logic):
#             self.write("'%s'" % node.value)
#         elif isinstance(node.vhd, vhd_boolean):
#             self.write("%s" % bool(node.value))
#         elif isinstance(node.vhd, (vhd_unsigned, vhd_signed)):
#             self.write('"%s"' % bin(node.value, node.vhd.size))
#         elif isinstance(node.vhd, vhd_string):
#             self.write("string'(\"%s\")" % node.value)
#         else:
#             self.write(node.value)

    def visit_Num(self, node):
        n = node.n
        if isinstance(node.vhd, vhd_std_logic):
            self.write("'%s'" % n)
        elif isinstance(node.vhd, vhd_boolean):
            self.write("%s" % bool(n))
        elif isinstance(node.vhd, (vhd_unsigned, vhd_signed)):
            self.write('"%s"' % bin(n, node.vhd.size))
        else:
            if n < 0:
                self.write("(")
            self.write(n)
            if n < 0:
                self.write(")")
            
    def visit_Str(self, node):
        self.write("string'(\"%s\")" % node.s)

#     def visitContinue(self, node, *args):
#         # self.write("next %s;" % self.labelStack[-1])
#         self.write("next;")


    def visit_Continue(self, node, *args):
       self.write("next;")


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
        # docstrings on unofficial places
        if isinstance(expr, ast.Str):
            doc = _makeDoc(expr.s, self.ind)
            self.write(doc)
            return
        # skip extra semicolons
        if isinstance(expr, ast.Num):
            return
        self.visit(expr)
        # ugly hack to detect an orphan "task" call
        if isinstance(expr, ast.Call) and hasattr(expr, 'tree'):
            self.write(';')
            

    def visit_IfExp(self, node):
        pre, suf = self.inferCast(node.vhd, node.body.vhdOri)
        self.write(pre)
        self.visit(node.body)
        self.write(suf)
        self.write(' when ')
        self.visit(node.test)
        self.write(' else ')
        pre, suf = self.inferCast(node.vhd, node.orelse.vhdOri)
        self.write(pre)
        self.visit(node.orelse)
        self.write(suf)


#     def visitFor(self, node, *args):
#         self.labelStack.append(node.breakLabel)
#         self.labelStack.append(node.loopLabel)
#         var = node.assign.name
#         cf = node.list
#         f = self.getObj(cf.node)
#         args = cf.args
#         assert len(args) <= 3
#         self.require(node, len(args) < 3, "explicit step not supported")
#         if f is range:
#             cmp = '<'
#             op = 'to'
#             oneoff = ''
#             if len(args) == 1:
#                 start, stop, step = None, args[0], None
#             elif len(args) == 2:
#                 start, stop, step = args[0], args[1], None
#             else:
#                 start, stop, step = args
#         else: # downrange
#             cmp = '>='
#             op = 'downto'
#             oneoff ='-1'
#             if len(args) == 1:
#                 start, stop, step = args[0], None, None
#             elif len(args) == 2:
#                 start, stop, step = args[0], args[1], None
#             else:
#                 start, stop, step = args
#         assert step is None
#  ##        if node.breakLabel.isActive:
# ##             self.write("begin: %s" % node.breakLabel)
# ##             self.writeline()
# ##         if node.loopLabel.isActive:
# ##             self.write("%s: " % node.loopLabel)
#         self.write("for %s in " % var)
#         if start is None:
#             self.write("0")
#         else:
#             self.visit(start)
#             if f is downrange:
#                 self.write("-1")
#         self.write(" %s " % op)
#         if stop is None:
#             self.write("0")
#         else:
#             self.visit(stop)
#             if f is range:
#                 self.write("-1")
#         self.write(" loop")
#         self.indent()
#         self.visit(node.body)
#         self.dedent()
#         self.writeline()
#         self.write("end loop;")
# ##         if node.breakLabel.isActive:
# ##             self.writeline()
# ##             self.write("end")
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
        self.require(node, len(args) < 3, "explicit step not supported")
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
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end loop;")
##         if node.breakLabel.isActive:
##             self.writeline()
##             self.write("end")
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



#     def mapToCase(self, node, *args):
#         var = node.caseVar
#         self.write("case ")
#         self.visit(var)
#         self.write(" is")
#         self.indent()
#         for test, suite in node.tests:
#             self.writeline()
#             item = test.ops[0][1].obj
#             self.write("when ")
#             self.write(item._toVHDL())
#             self.write(" =>")
#             self.indent()
#             self.visit(suite)
#             self.dedent()
#         if node.else_:
#             self.writeline()
#             self.write("when others =>")
#             self.indent()
#             self.visit(node.else_)
#             self.dedent()
#         self.dedent()
#         self.writeline()
#         self.write("end case;")

    def mapToCase(self, node):
        var = node.caseVar
        obj = self.getObj(var)
        self.write("case ")
        self.visit(var)
        self.write(" is")
        self.indent()
        for test, suite in node.tests:
            self.writeline()
            item = test.case[1]
            self.write("when ")
            if isinstance(item, EnumItemType):
                self.write(item._toVHDL())
            else:
                self.write(self.BitRepr(item, obj))
            self.write(" =>")
            self.indent()
            self.visit_stmt(suite)
            self.dedent()
        if node.else_:
            self.writeline()
            self.write("when others =>")
            self.indent()
            self.visit_stmt(node.else_)
            self.dedent()
        self.dedent()
        self.writeline()
        self.write("end case;")


        
#     def mapToIf(self, node, *args):
#         first = True
#         for test, suite in node.tests:
#             if first:
#                 ifstring = "if "
#                 first = False
#             else:
#                 ifstring = "elsif "
#                 self.writeline()
#             self.write(ifstring)
#             self.visit(test, _context.BOOLEAN)
#             self.write(" then")
#             self.indent()
#             self.visit(suite)
#             self.dedent()
#         if node.else_:
#             self.writeline()
#             edges = self.getEdge(node.else_)
#             if edges is not None:
#                 edgeTests = [e._toVHDL() for e in edges]
#                 self.write("elsif ")
#                 self.write("or ".join(edgeTests))
#                 self.write(" then")
#             else:
#                 self.write("else")
#             self.indent()
#             self.visit(node.else_)
#             self.dedent()
#         self.writeline()
#         self.write("end if;")

    def mapToIf(self, node):
        first = True
        for test, suite in node.tests:
            if first:
                ifstring = "if "
                first = False
            else:
                ifstring = "elsif "
                self.writeline()
            self.write(ifstring)
            self.visit(test)
            self.write(" then")
            self.indent()
            self.visit_stmt(suite)
            self.dedent()
        if node.else_:
            self.writeline()
            edges = self.getEdge(node)
            if edges is not None:
                edgeTests = [e._toVHDL() for e in edges]
                self.write("elsif ")
                self.write("or ".join(edgeTests))
                self.write(" then")
            else:
                self.write("else")
            self.indent()
            self.visit_stmt(node.else_)
            self.dedent()
        self.writeline()
        self.write("end if;")






#     def visitKeyword(self, node, *args):
#         self.visit(node.expr)



    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)


#     def visitAssName(self, node, *args):
#         self.write(node.name)
       

#     def visitName(self, node, context=None, *args):
#         n = node.name
#         if n == 'False':
#             if isinstance(node.vhd, vhd_std_logic):
#                 s = "'0'"
#             else:
#                 s = "False"
#         elif n == 'True':
#             if isinstance(node.vhd, vhd_std_logic):
#                 s = "'1'"
#             else:
#                 s = "True"
#         elif n in self.tree.vardict:
#             s = n
#             obj = self.tree.vardict[n]
#             ori = inferVhdlObj(obj)
#             pre, suf = self.inferCast(node.vhd, ori)
#             s = "%s%s%s" % (pre, s, suf)
                       
#         elif n in self.tree.argnames:
#             assert n in self.tree.symdict
#             obj = self.tree.symdict[n]
#             vhd = inferVhdlObj(obj)
#             if isinstance(vhd, vhd_std_logic) and isinstance(node.vhd, vhd_boolean):
#                 s = "(%s = '1')" %  n
#             else:
#                 s = n
#         elif n in self.tree.symdict:
#             obj = self.tree.symdict[n]
#             s = n
#             if isinstance(obj, bool):
#                 s = "'%s'" % int(obj)
#             elif isinstance(obj, (int, long)):
#                 if isinstance(node.vhd, vhd_int):
#                     if obj >= 0:
#                         s = "%s" % int(obj)
#                     else:
#                         s = "(- %s)" % abs(int(obj))
#                 elif isinstance(node.vhd, vhd_std_logic):
#                     s = "'%s'" % int(obj)
#                 else:
#                     s = '"%s"' % bin(obj, node.vhd.size)
#             elif isinstance(obj, Signal):
#                 if context == _context.PRINT:
#                     pass
# ##                     if obj._type is intbv:
# ##                         s = "write(L, to_integer(%s))" % str(obj)
# ##                     elif obj._type is bool:
# ##                         s = "write(L, to_bit(%s))" % str(obj)
# ##                     else:
# ##                         typename = "UNDEF"
# ##                         if isinstance(obj._val, EnumItemType):
# ##                             typename = obj._val._type._name
# ##                         s = "write(L, %s'image(%s))" % (typename, str(obj))
#                 s = str(obj)
#                 ori = inferVhdlObj(obj)
#                 pre, suf = self.inferCast(node.vhd, ori)
#                 s = "%s%s%s" % (pre, s, suf)
                       
#             elif _isMem(obj):
#                 m = _getMemInfo(obj)
#                 assert m.name
#                 s = m.name
#             elif isinstance(obj, EnumItemType):
#                 s = obj._toVHDL()
#             elif type(obj) is ClassType and issubclass(obj, Exception):
#                 s = n
#             else:
#                 self.raiseError(node, _error.UnsupportedType, "%s, %s" % (n, type(obj)))
#         else:
#             raise AssertionError("name ref: %s" % n)
#         self.write(s)



    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setName(node)
        else:
            self.getName(node)

    def setName(self, node):
        self.write(node.id)

    def getName(self, node):
        n = node.id
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
        elif n == 'None':
            s = "(others => 'Z')"
        elif n in self.tree.vardict:
            s = n
            obj = self.tree.vardict[n]
            ori = inferVhdlObj(obj)
            pre, suf = self.inferCast(node.vhd, ori)
            s = "%s%s%s" % (pre, s, suf)
                       
        elif n in self.tree.argnames:
            assert n in self.tree.symdict
            obj = self.tree.symdict[n]
            vhd = inferVhdlObj(obj)
            if isinstance(vhd, vhd_std_logic) and isinstance(node.vhd, vhd_boolean):
                s = "(%s = '1')" %  n
            else:
                s = n
        elif n in self.tree.symdict:
            obj = self.tree.symdict[n]
            s = n
            if isinstance(obj, bool):
                s = "'%s'" % int(obj)
            elif isinstance(obj, (int, long)):
                if isinstance(node.vhd, vhd_int):
                    s = self.IntRepr(obj)
                elif isinstance(node.vhd, vhd_std_logic):
                    s = "'%s'" % int(obj)
                else:
                    s = '"%s"' % bin(obj, node.vhd.size)
            elif isinstance(obj, _Signal):
                s = str(obj)
                ori = inferVhdlObj(obj)
                # print 'name', n
                pre, suf = self.inferCast(node.vhd, ori)
                s = "%s%s%s" % (pre, s, suf)
            elif _isMem(obj):
                m = _getMemInfo(obj)
                assert m.name
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


#     def visitPass(self, node, *args):
#         self.write("null;")

    def visit_Pass(self, node):
        self.write("null;")



##     def handlePrint(self, node):
##         assert len(node.nodes) == 1
##         s = node.nodes[0]
##         if isinstance(s.vhdOri, vhd_vector):
##             s.vhd = vhd_int()
##         elif isinstance(s.vhdOri, vhd_std_logic):
##             s.vhd = vhd_string()
##         elif isinstance(s.vhdOri, vhd_enum):
##             s.vhd = vhd_string()
##         self.write("write(L, ")
##         self.visit(s, _context.PRINT)
##         self.write(")")
##         self.write(';')
##         self.writeline()
##         self.write("writeline(output, L);")
        
    
##     def visitPrint(self, node, *args):
##         self.handlePrint(node)

#     def visitPrintnl(self, node, *args):
# ##         self.handlePrint(node)
#         argnr = 0
#         for s in node.format:
#             if isinstance(s, str):
#                 self.write('write(L, string\'("%s"));' % s)
#             else:
#                 a = node.args[argnr]
#                 argnr += 1
#                 if s.conv is int:
#                     a.vhd = vhd_int()
#                 else:
#                     if isinstance(a.vhdOri, vhd_vector):
#                         a.vhd = vhd_int()
#                     elif isinstance(a.vhdOri, vhd_std_logic):
#                         a.vhd = vhd_boolean()
#                     elif isinstance(a.vhdOri, vhd_enum):
#                         a.vhd = vhd_string()
#                 self.write("write(L, ")
#                 self.visit(a, _context.PRINT)
#                 if s.justified == 'LEFT':
#                     self.write(", justified=>LEFT")
#                 if s.width:
#                     self.write(", field=>%s" % s.width)
#                 self.write(")")
#                 self.write(';')
#             self.writeline()
#         self.write("writeline(output, L);")


    def visit_Print(self, node):
        argnr = 0
        for s in node.format:
            if isinstance(s, str):
                self.write('write(L, string\'("%s"));' % s)
            else:
                a = node.args[argnr]
                argnr += 1
                if s.conv is int:
                    a.vhd = vhd_int()
                else:
                    if isinstance(a.vhdOri, vhd_vector):
                        a.vhd = vhd_int()
                    elif isinstance(a.vhdOri, vhd_std_logic):
                        a.vhd = vhd_boolean()
                    elif isinstance(a.vhdOri, vhd_enum):
                        a.vhd = vhd_string()
                self.write("write(L, ")
                self.context = _context.PRINT
                self.visit(a)
                self.context = None
                if s.justified == 'LEFT':
                    self.write(", justified=>LEFT")
                if s.width:
                    self.write(", field=>%s" % s.width)
                self.write(")")
                self.write(';')
            self.writeline()
        self.write("writeline(output, L);")


                
               
    
#     def visitRaise(self, node, *args):
# #        pass
#         self.write('assert False report "End of Simulation" severity Failure;')
# ##         self.write('$display("')
# ##         self.visit(node.expr1)
# ##         self.write('");')
# ##         self.writeline()
# ##         self.write("$finish;")

    def visit_Raise(self, node):
        self.write('assert False report "End of Simulation" severity Failure;')
        
#     def visitReturn(self, node, *args):
#         self.write("disable %s;" % self.returnLabel)

    def visit_Return(self, node):
        pass

    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)


#     def visitSlice(self, node, context=None, *args):
#         if isinstance(node.expr, astNode.CallFunc) and \
#            node.expr.node.obj is intbv and \
#            _isConstant(node.expr.args[0], self.tree.symdict):
#             c = self.getVal(node)._val
#             pre, post = "", ""
#             if node.vhd.size <= 30:
#                 if isinstance(node.vhd, vhd_unsigned):
#                     pre, post = "to_unsigned(", ", %s)" % node.vhd.size
#                 elif isinstance(node.vhd, vhd_signed):
#                     pre, post = "to_signed(", ", %s)" % node.vhd.size
#             else:
#                 if isinstance(node.vhd, vhd_unsigned):
#                     pre, post = "unsigned'(", ")"
#                     c = '"%s"' % bin(c, node.vhd.size)
#                 elif isinstance(node.vhd, vhd_signed):
#                     pre, post = "signed'(", ")"
#                     c = '"%s"' % bin(c, node.vhd.size)
#             self.write(pre)
#             self.write("%s" % c)
#             self.write(post)
#             return
#         pre, suf = self.inferCast(node.vhd, node.vhdOri)
#         if isinstance(node.expr.vhd, vhd_signed) and node.flags != 'OP_ASSIGN':
#             pre = pre + "unsigned("
#             suf = ")" + suf
#         self.write(pre)
#         self.visit(node.expr)
#         # special shortcut case for [:] slice
#         if node.lower is None and node.upper is None:
#             self.write(suf)
#             return
#         self.write("(")
#         if node.lower is None:
#             self.write("%s" % node.obj._nrbits)
#         else:
#             self.visit(node.lower)
#         self.write("-1 downto ")
#         if node.upper is None:
#             self.write("0")
#         else:
#             self.visit(node.upper)
#         self.write(")")
#         self.write(suf)


    def accessSlice(self, node):
        if isinstance(node.value, ast.Call) and \
           node.value.func.obj is intbv and \
           _isConstant(node.value.args[0], self.tree.symdict):
            c = self.getVal(node)._val
            pre, post = "", ""
            if node.vhd.size <= 30:
                if isinstance(node.vhd, vhd_unsigned):
                    pre, post = "to_unsigned(", ", %s)" % node.vhd.size
                elif isinstance(node.vhd, vhd_signed):
                    pre, post = "to_signed(", ", %s)" % node.vhd.size
            else:
                if isinstance(node.vhd, vhd_unsigned):
                    pre, post = "unsigned'(", ")"
                    c = '"%s"' % bin(c, node.vhd.size)
                elif isinstance(node.vhd, vhd_signed):
                    pre, post = "signed'(", ")"
                    c = '"%s"' % bin(c, node.vhd.size)
            self.write(pre)
            self.write("%s" % c)
            self.write(post)
            return
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        if isinstance(node.value.vhd, vhd_signed) and isinstance(node.ctx, ast.Load):
            pre = pre + "unsigned("
            suf = ")" + suf
        self.write(pre)
        self.visit(node.value)
        lower, upper = node.slice.lower, node.slice.upper
         # special shortcut case for [:] slice
        if lower is None and upper is None:
            self.write(suf)
            return
        self.write("(")
        if lower is None:
            self.write("%s" % node.obj._nrbits)
        else:
            self.visit(lower)
        self.write("-1 downto ")
        if upper is None:
            self.write("0")
        else:
            self.visit(upper)
        self.write(")")
        self.write(suf)


#     def visitSubscript(self, node, context=None, *args):
#         pre, suf = self.inferCast(node.vhd, node.vhdOri)
#         self.write(pre)
#         self.visit(node.expr)
#         self.write("(")
#         assert len(node.subs) == 1
#         self.visit(node.subs[0])
#         self.write(")")
#         self.write(suf)

    def accessIndex(self, node):
        pre, suf = self.inferCast(node.vhd, node.vhdOri)
        self.write(pre)
        self.visit(node.value)
        self.write("(")
        #assert len(node.subs) == 1
        self.visit(node.slice.value)
        self.write(")")
        self.write(suf)


#     def visitStmt(self, node, *args):
#         for stmt in node.nodes:
#             self.writeline()
#             self.visit(stmt)
#             # ugly hack to detect an orphan "task" call
#             if isinstance(stmt, astNode.CallFunc) and hasattr(stmt, 'tree'):
#                 self.write(';')

    def visit_stmt(self, body):
        for stmt in body:
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
#         self.write("while ")
#         self.visit(node.test)
#         self.write(" loop")
#         self.indent()
#         self.visit(node.body)
#         self.dedent()
#         self.writeline()
#         self.write("end loop")
#         self.write(";")
#         self.labelStack.pop()
#         self.labelStack.pop()


    def visit_While(self, node):
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.write("while ")
        self.visit(node.test)
        self.write(" loop")
        self.indent()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end loop")
        self.write(";")
        self.labelStack.pop()
        self.labelStack.pop()




        
#     def visitYield(self, node, *args):
#         self.write("wait ")
#         yieldObj = self.getObj(node.value)
#         if isinstance(yieldObj, delay):
#             self.write("for ")
#         elif isinstance(yieldObj, _WaiterList):
#             self.write("until ")
#         else:
#             self.write("on ")
#         self.visit(node.value, _context.YIELD)
#         self.write(";")

    def visit_Yield(self, node):
        self.write("wait ")
        yieldObj = self.getObj(node.value)
        if isinstance(yieldObj, delay):
            self.write("for ")
        elif isinstance(yieldObj, _WaiterList):
            self.write("until ")
        else:
            self.write("on ")
        self.context = _context.YIELD
        self.visit(node.value)
        self.context = _context.UNKNOWN
        self.write(";")





    def manageEdges(self, ifnode, senslist):
        """ Helper method to convert MyHDL style template into VHDL style"""
        first = senslist[0]
        if isinstance(first, _WaiterList):
            bt = _WaiterList
        elif isinstance(first, _Signal):
            bt = _Signal
        elif isinstance(first, delay):
            bt  = delay
        assert bt
        for e in senslist:
            if not isinstance(e, bt):
                self.raiseError(ifnode, "base type error in sensitivity list")
        if len(senslist) >= 2 and bt == _WaiterList:
            # ifnode = node.code.nodes[0]
            # print ifnode
            assert isinstance(ifnode, ast.If)
            asyncEdges = []
            for test, suite in ifnode.tests:
                e = self.getEdge(test)
                if e is None:
                    self.raiseError(ifnode, "No proper edge value test")
                asyncEdges.append(e)
            if not ifnode.else_:
                self.raiseError(ifnode, "No separate else clause found")
            edges = []
            for s in senslist:
                for e in asyncEdges:
                    if s is e:
                        break
                else:
                    edges.append(s)
            ifnode.edge = edges
            senslist = [s.sig for s in senslist]
        return senslist



            
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
#         senslist = y.senslist
#         senslist = self.manageEdges(w.body.nodes[1], senslist)
#         singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
#         self.write("%s: process (" % self.tree.name)
#         if singleEdge:
#             self.write(senslist[0].sig)
#         else:
#             for e in senslist[:-1]:
#                 self.write(e)
#                 self.write(', ')
#             self.write(senslist[-1])
#         self.write(") is")
#         self.indent()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         if singleEdge:
#             self.writeline()
#             self.write("if %s then" % senslist[0]._toVHDL())
#             self.indent()
#         assert isinstance(w.body, astNode.Stmt)
#         for stmt in w.body.nodes[1:]:
#             self.writeline()
#             self.visit(stmt)
#         self.dedent()
#         if singleEdge:
#             self.writeline()
#             self.write("end if;")
#             self.dedent()
#         self.writeline()
#         self.write("end process %s;" % self.tree.name)
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        w = node.body[-1]
        y = w.body[0]
        if isinstance(y, ast.Expr):
            y = y.value
        assert isinstance(y, ast.Yield)
        senslist = y.senslist
        senslist = self.manageEdges(w.body[1], senslist)
        singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
        self.write("%s: process (" % self.tree.name)
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
        # assert isinstance(w.body, ast.stmt)
        for stmt in w.body[1:]:
            self.writeline()
            self.visit(stmt)
        self.dedent()
        if singleEdge:
            self.writeline()
            self.write("end if;")
            self.dedent()
        self.writeline()
        self.write("end process %s;" % self.tree.name)
        self.writeline(2)



        
    
class _ConvertInitialVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         self.write("%s: process is" % self.tree.name)
#         self.indent()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         self.visit(node.code)
#         self.writeline()
#         self.write("wait;")
#         self.dedent()
#         self.writeline()
#         self.write("end process %s;" % self.tree.name)
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.write("%s: process is" % self.tree.name)
        self.indent()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin")
        self.indent()
        self.visit_stmt(node.body)
        self.writeline()
        self.write("wait;")
        self.dedent()
        self.writeline()
        self.write("end process %s;" % self.tree.name)
        self.writeline(2)




class _ConvertAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         senslist = self.tree.senslist
#         self.write("%s: process (" % self.tree.name)
#         for e in senslist[:-1]:
#             self.write(e)
#             self.write(', ')
#         self.write(senslist[-1])
#         self.write(") is")
#         self.indent()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end process %s;" % self.tree.name)
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        senslist = self.tree.senslist
        self.write("%s: process (" % self.tree.name)
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
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end process %s;" % self.tree.name)
        self.writeline(2)


        
class _ConvertSimpleAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitAssAttr(self, node, *args):
#         self.visit(node.expr)
#         self.isSigAss = True


    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.visit(node.value)
            self.isSigAss = True
        else:
            self.getAttr(node)


#     def visitFunction(self, node, *args):
#         self.visit(node.code)
#         self.writeline(2)

    def visit_FunctionDef(self, node, *args):
        self.writeDoc(node)
        self.visit_stmt(node.body)
        self.writeline(2)



        
class _ConvertAlwaysDecoVisitor(_ConvertVisitor):
    
    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

#     def visitFunction(self, node, *args):
#         assert self.tree.senslist
#         senslist = self.tree.senslist
#         senslist = self.manageEdges(node.code.nodes[-1], senslist)
#         singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
#         self.write("%s: process (" % self.tree.name)
#         if singleEdge:
#             self.write(senslist[0].sig)
#         else:
#             for e in senslist[:-1]:
#                 self.write(e)
#                 self.write(', ')
#             self.write(senslist[-1])
#         self.write(") is")
#         self.indent()
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         if singleEdge:
#             self.writeline()
#             self.write("if %s then" % senslist[0]._toVHDL())
#             self.indent()
#         self.visit(node.code)
#         self.dedent()
#         if singleEdge:
#             self.writeline()
#             self.write("end if;")
#             self.dedent()
#         self.writeline()
#         self.write("end process %s;" % self.tree.name)
#         self.writeline(2)


    def visit_FunctionDef(self, node, *args):
        self.writeDoc(node)
        assert self.tree.senslist
        senslist = self.tree.senslist
        senslist = self.manageEdges(node.body[-1], senslist)
        singleEdge = (len(senslist) == 1) and isinstance(senslist[0], _WaiterList)
        self.write("%s: process (" % self.tree.name)
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
        self.visit_stmt(node.body)
        self.dedent()
        if singleEdge:
            self.writeline()
            self.write("end if;")
            self.dedent()
        self.writeline()
        self.write("end process %s;" % self.tree.name)
        self.writeline(2)





       
    
class _ConvertFunctionVisitor(_ConvertVisitor):
    
    def __init__(self, tree, funcBuf):
        _ConvertVisitor.__init__(self, tree, funcBuf)
        self.returnObj = tree.returnObj
        self.returnLabel = _Label("RETURN")

    def writeOutputDeclaration(self):
        self.write(self.tree.vhd.toStr(constr=False))

    def writeInputDeclarations(self):
        endchar = ""
        for name in self.tree.argnames:
            self.write(endchar)
            endchar = ";"
            obj = self.tree.symdict[name]
            self.writeline()
            self.writeDeclaration(obj, name, dir="in", constr=False, endchar="")
            
#     def visitFunction(self, node, *args):
#         self.write("function %s(" % self.tree.name)
#         self.indent()
#         self.writeInputDeclarations()
#         self.writeline()
#         self.write(") return ")
#         self.writeOutputDeclaration()
#         self.write(" is")
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end function %s;" % self.tree.name)
#         self.writeline(2)

    def visit_FunctionDef(self, node):
        self.write("function %s(" % self.tree.name)
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
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end function %s;" % self.tree.name)
        self.writeline(2)


#     def visitReturn(self, node, *args):
#         self.write("return ")
#         self.visit(node.value)
#         self.write(";")

    def visit_Return(self, node):
        self.write("return ")
        self.visit(node.value)
        self.write(";")


    
    
class _ConvertTaskVisitor(_ConvertVisitor):
    
    def __init__(self, tree, funcBuf):
        _ConvertVisitor.__init__(self, tree, funcBuf)
        self.returnLabel = _Label("RETURN")

    def writeInterfaceDeclarations(self):
        endchar = ""
        for name in self.tree.argnames:
            self.write(endchar)
            endchar = ";"
            obj = self.tree.symdict[name]
            output = name in self.tree.outputs
            input = name in self.tree.inputs
            inout = input and output
            dir = (inout and "inout") or (output and "out") or "in"
            self.writeline()
            self.writeDeclaration(obj, name, dir=dir, constr=False, endchar="")
            
#     def visitFunction(self, node, *args):
#         self.write("procedure %s" % self.tree.name)
#         if self.tree.argnames:
#             self.write("(")
#             self.indent()
#             self.writeInterfaceDeclarations()
#             self.write(") ")
#         self.write("is")
#         self.writeDeclarations()
#         self.dedent()
#         self.writeline()
#         self.write("begin")
#         self.indent()
#         t = node.code.nodes[0].tests[0][0]
#         self.visit(node.code)
#         self.dedent()
#         self.writeline()
#         self.write("end procedure %s;" % self.tree.name)
#         self.writeline(2)


    def visit_FunctionDef(self, node):
        self.write("procedure %s" % self.tree.name)
        if self.tree.argnames:
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
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end procedure %s;" % self.tree.name)
        self.writeline(2)




# type inference

class vhd_type(object):
    def __init__(self, size=0):
        self.size = size
    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.size)

class vhd_string(vhd_type):
    pass

class vhd_enum(vhd_type):
    def __init__(self, tipe):
        self._type = tipe
        
class vhd_std_logic(vhd_type):
    def __init__(self, size=0):
        vhd_type.__init__(self)
        self.size = 1
    def toStr(self, constr=True):
        return 'std_logic'
        
class vhd_boolean(vhd_type):
    def __init__(self, size=0):
        vhd_type.__init__(self)
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

class vhd_nat(vhd_int):
    def toStr(self, constr=True):
        return "natural"
    

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
    if (isinstance(obj, _Signal) and obj._type is intbv) or \
       isinstance(obj, intbv):
        if obj.min < 0:
            vhd = vhd_signed(len(obj))
        else:
            vhd = vhd_unsigned(len(obj))
    elif (isinstance(obj, _Signal) and obj._type is bool) or \
         isinstance(obj, bool):
        vhd = vhd_std_logic()
    elif (isinstance(obj, _Signal) and isinstance(obj._val, EnumItemType)) or\
         isinstance(obj, EnumItemType):
        if isinstance(obj, _Signal):
            tipe = obj._val._type
        else:
            tipe = obj._type
        vhd = vhd_enum(tipe)   
    elif isinstance(obj, (int, long)):
        if obj >= 0:
            vhd = vhd_nat()
        else:
            vhd = vhd_int()
        # vhd = vhd_int()
    return vhd

def maybeNegative(vhd):
    if isinstance(vhd, vhd_signed):
        return True
    if isinstance(vhd, vhd_int) and not isinstance(vhd, vhd_nat):
        return True
    return False

        
class _AnnotateTypesVisitor(ast.NodeVisitor, _ConversionMixin):

    def __init__(self, tree):
        self.tree = tree

    def visit_FunctionDef(self, node):
       # don't visit arguments and decorators
       for stmt in node.body:
           self.visit(stmt)

#     def visitAssAttr(self, node):
#         self.visit(node.expr)
#         node.vhd = copy(node.expr.vhd)

#     def visitGetattr(self, node):
#         self.visitChildNodes(node)
#         node.vhd = copy(node.expr.vhd)
#         node.vhdOri = copy(node.vhd)

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.vhd = copy(node.value.vhd)
        node.vhdOri = copy(node.vhd)

    
#     def visitAssert(self, node):
#         self.visit(node.test)
#         node.test.vhd = vhd_boolean()

    def visit_Assert(self, node):
        self.visit(node.test)
        node.test.vhd = vhd_boolean()

                   
#     def visitAugAssign(self, node):
#         self.visit(node.node)
#         self.visit(node.expr)
#         if node.op in ("|=", "&=", "^="):
#             node.expr.vhd = copy(node.node.vhd)
#             node.vhdOri = node.node.vhd
#         elif node.op in ("<<=", ">>="):
#             node.expr.vhd = vhd_int()           
#             node.vhdOri = copy(node.node.vhd)
#         else:
#              left, right = node.node, node.expr
#              self.inferBinaryOpType(node, left, right, node.op)
#         node.vhd = copy(node.node.vhd)


    def visit_AugAssign(self, node):
        self.visit(node.target)
        self.visit(node.value)
        if isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor)):
            node.value.vhd = copy(node.target.vhd)
            node.vhdOri = copy(node.target.vhd)
        elif isinstance(node.op, (ast.RShift, ast.LShift)):
            node.value.vhd = vhd_int()           
            node.vhdOri = copy(node.target.vhd)
        else:
             node.left, node.right = node.target, node.value
             self.inferBinOpType(node)
        node.vhd = copy(node.target.vhd)

        
#     def visitCallFunc(self, node):
#         fn = node.node
#         # assert isinstance(fn, astNode.Name)
#         f = self.getObj(fn)
#         node.vhd = inferVhdlObj(node.obj)
#         self.visitChildNodes(node)
#         if f is concat:
#             s = 0
#             for a in node.args:
#                 s += a.vhd.size
#             node.vhd = vhd_unsigned(s)
#         elif f is bool:
#             node.vhd = vhd_boolean()
#         elif f in (int, long, ord):
#             node.vhd = vhd_int()
#             node.args[0].vhd = vhd_int()
#         elif f is intbv:
#             node.vhd = vhd_int()
#         elif f is len:
#             node.vhd = vhd_int()
#         elif f is now:
#             node.vhd = vhd_nat()
#         elif f == intbv.signed: # note equality comparison
#             # this comes from a getattr
#             node.vhd = vhd_signed(fn.expr.vhd.size)
#         elif hasattr(node, 'tree'):
#             v = _AnnotateTypesVisitor(node.tree)
#             compiler.walk(node.tree, v)
#             node.vhd = node.tree.vhd = inferVhdlObj(node.tree.returnObj)
#         node.vhdOri = copy(node.vhd)

    def visit_Call(self, node):
        fn = node.func
        # assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        node.vhd = inferVhdlObj(node.obj)
        self.generic_visit(node)
        if f is concat:
            s = 0
            for a in node.args:
                s += a.vhd.size
            node.vhd = vhd_unsigned(s)
        elif f is bool:
            node.vhd = vhd_boolean()
        elif f in (int, long, ord):
            node.vhd = vhd_int()
            node.args[0].vhd = vhd_int()
        elif f is intbv:
            node.vhd = vhd_int()
        elif f is len:
            node.vhd = vhd_int()
        elif f is now:
            node.vhd = vhd_nat()
        elif f == intbv.signed: # note equality comparison
            # this comes from a getattr
            node.vhd = vhd_signed(fn.value.vhd.size)
        elif hasattr(node, 'tree'):
            v = _AnnotateTypesVisitor(node.tree)
            v.visit(node.tree)
            node.vhd = node.tree.vhd = inferVhdlObj(node.tree.returnObj)
        node.vhdOri = copy(node.vhd)

    
#     def visitCompare(self, node):
#         node.vhd = vhd_boolean()
#         self.visitChildNodes(node)
#         expr = node.expr
#         op, code = node.ops[0]
#         if isinstance(expr.vhd, vhd_std_logic) or isinstance(node.vhd, vhd_std_logic):
#             expr.vhd = code.vhd = vhd_std_logic()
#         elif isinstance(expr.vhd, vhd_unsigned) and maybeNegative(code.vhd):
#             expr.vhd = vhd_signed(expr.vhd.size + 1)
#         elif maybeNegative(expr.vhd) and isinstance(code.vhd, vhd_unsigned):
#             code.vhd = vhd_signed(code.vhd.size + 1)
#         node.vhdOri = copy(node.vhd)


    def visit_Compare(self, node):
        node.vhd = vhd_boolean()
        self.generic_visit(node)
        left, op, right = node.left, node.ops[0], node.comparators[0]
        if isinstance(left.vhd, vhd_std_logic) or isinstance(right.vhd, vhd_std_logic):
            left.vhd = right.vhd = vhd_std_logic()
        elif isinstance(left.vhd, vhd_unsigned) and maybeNegative(right.vhd):
            left.vhd = vhd_signed(left.vhd.size + 1)
        elif maybeNegative(left.vhd) and isinstance(right.vhd, vhd_unsigned):
            right.vhd = vhd_signed(right.vhd.size + 1)
        node.vhdOri = copy(node.vhd)


#     def visitConst(self, node):
#         if isinstance(node.value, str):
#             node.vhd = vhd_string()
#         else:
#             node.vhd = vhd_nat()
#         node.vhdOri = copy(node.vhd)

    def visit_Str(self, node):
        node.vhd = vhd_string()
        node.vhdOri = copy(node.vhd)

    def visit_Num(self, node):
        if node.n < 0:
            node.vhd = vhd_int()
        else:
            node.vhd = vhd_nat()
        node.vhdOri = copy(node.vhd)

#     def visitFor(self, node):
#         var = node.assign.name
#         # make it possible to detect loop variable
#         self.tree.vardict[var] = _loopInt(-1)
#         self.visitChildNodes(node)


    def visit_For(self, node):
        var = node.target.id
        # make it possible to detect loop variable
        self.tree.vardict[var] = _loopInt(-1)
        self.generic_visit(node)
  
#     def visitName(self, node):
#         node.vhd = inferVhdlObj(node.obj)
#         node.vhdOri = copy(node.vhd)
  
#     # visitAssName = visitName
#     def visitAssName(self, node):
#         node.obj = self.tree.vardict[node.name]
#         self.visitName(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            node.obj = self.tree.vardict[node.id]
        node.vhd = inferVhdlObj(node.obj)
        node.vhdOri = copy(node.vhd)
     

#     def binaryOp(self, node, op=None):
#         self.visit(node.left)
#         self.visit(node.right)
#         left, right = node.left, node.right
#         self.inferBinaryOpType(node, left, right, op)

#     def inferBinaryOpType(self, node, left, right, op=None):
#         if isinstance(left.vhd, (vhd_boolean, vhd_std_logic)):
#             left.vhd = vhd_unsigned(1)
#         if isinstance(right.vhd, (vhd_boolean, vhd_std_logic)):
#             right.vhd = vhd_unsigned(1)
#         if maybeNegative(left.vhd) and isinstance(right.vhd, vhd_unsigned):
#             right.vhd = vhd_signed(right.vhd.size + 1)
#         if isinstance(left.vhd, vhd_unsigned) and maybeNegative(right.vhd):
#             left.vhd = vhd_signed(left.vhd.size + 1)
#         l, r = left.vhd, right.vhd
#         ls, rs = l.size, r.size       
#         if isinstance(r, vhd_vector) and isinstance(l, vhd_vector):
#             if op in ('+', '-', '+=', '-='):
#                 s = max(ls, rs)
#             elif op in ('%', '%='):
#                 s = rs
#             elif op in ('/', '//='):
#                 s = ls
#             elif op in ('*', '*='):
#                 s = ls + rs
#             else:
#                 raise AssertionError("unexpected op %s" % op)
#         elif isinstance(l, vhd_vector) and isinstance(r, vhd_int):
#             if op in ('+', '-', '%', '/', '+=', '-=', '%=', '//='):
#                 s = ls
#             elif op in ('*' , '*='):
#                  s = 2 * ls
#             else:
#                 raise AssertionError("unexpected op %s" % op)
#         elif isinstance(l, vhd_int) and isinstance(r, vhd_vector):
#             if op in ('+', '-', '%', '/', '+=', '-=', '%=', '//='):
#                 s = rs
#             elif op in ('*' , '*='):
#                 s = 2 * rs
#             else:
#                 raise AssertionError("unexpected op %s" % op)
#         if isinstance(l, vhd_int) and isinstance(r, vhd_int):
#             node.vhd = vhd_int()
#         elif isinstance(l, (vhd_signed, vhd_int)) and isinstance(r, (vhd_signed, vhd_int)):
#             node.vhd = vhd_signed(s)
#         elif isinstance(l, (vhd_unsigned, vhd_int)) and isinstance(r, (vhd_unsigned, vhd_int)):
#             node.vhd = vhd_unsigned(s)
#         else:
#             node.vhd = vhd_int()
#         node.vhdOri = copy(node.vhd)

#     def visitAdd(self, node):
#         self.binaryOp(node, op='+')
#     def visitSub(self, node):
#         self.binaryOp(node, op='-')
#     def visitMod(self, node):
#         # detect format string use
#         if (isinstance(node.left, astNode.Const) and isinstance(node.left.value, str)):
#             self.visit(node.left)
#             self.visit(node.right)
#         else:
#             self.binaryOp(node, op='%')
#     def visitMul(self, node):
#         self.binaryOp(node, op='*')
#     def visitFloorDiv(self, node):
#         self.binaryOp(node, op='/')

    
#     def multiBitOp(self, node):
#         self.visitChildNodes(node)
#         o = None
#         for n in node.nodes:
#             o = maxType(o, n.vhd)
#         for n in node.nodes:
#             n.vhd = o
#         node.vhd = o
#         node.vhdOri = copy(node.vhd)
#     visitBitand = visitBitor = visitBitxor = multiBitOp

    
#     def shift(self, node):
#         self.visitChildNodes(node)
#         node.vhd = copy(node.left.vhd)
#         node.right.vhd = vhd_nat()
#         node.vhdOri = copy(node.vhd)
#     visitRightShift = visitLeftShift = shift



    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            self.inferShiftType(node)
        elif isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)):
            self.inferBitOpType(node)
        elif isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str): # format string
            pass
        else:
            self.inferBinOpType(node)

    def inferShiftType(self, node):
        node.vhd = copy(node.left.vhd)
        node.right.vhd = vhd_nat()
        node.vhdOri = copy(node.vhd)


    def inferBitOpType(self, node):
        obj = maxType(node.left.vhd, node.right.vhd)
        node.vhd = node.left.vhd = node.right.vhd = obj
        node.vhdOri = copy(node.vhd)

    def inferBinOpType(self, node):
        left, op, right = node.left, node.op, node.right
        if isinstance(left.vhd, (vhd_boolean, vhd_std_logic)):
            left.vhd = vhd_unsigned(1)
        if isinstance(right.vhd, (vhd_boolean, vhd_std_logic)):
            right.vhd = vhd_unsigned(1)
        if maybeNegative(left.vhd) and isinstance(right.vhd, vhd_unsigned):
            right.vhd = vhd_signed(right.vhd.size + 1)
        if isinstance(left.vhd, vhd_unsigned) and maybeNegative(right.vhd):
            left.vhd = vhd_signed(left.vhd.size + 1)
        l, r = left.vhd, right.vhd
        ls, rs = l.size, r.size       
        if isinstance(r, vhd_vector) and isinstance(l, vhd_vector):
            if isinstance(op, (ast.Add, ast.Sub)):
                s = max(ls, rs)
            elif isinstance(op, ast.Mod):
                s = rs
            elif isinstance(op, ast.FloorDiv):
                s = ls
            elif isinstance(op, ast.Mult):
                s = ls + rs
            else:
                raise AssertionError("unexpected op %s" % op)
        elif isinstance(l, vhd_vector) and isinstance(r, vhd_int):
            if isinstance(op, (ast.Add, ast.Sub, ast.Mod, ast.FloorDiv)):
                s = ls
            elif isinstance(op, ast.Mult):
                 s = 2 * ls
            else:
                raise AssertionError("unexpected op %s" % op)
        elif isinstance(l, vhd_int) and isinstance(r, vhd_vector):
            if isinstance(op, (ast.Add, ast.Sub, ast.Mod, ast.FloorDiv)):
                s = rs
            elif isinstance(op, ast.Mult):
                s = 2 * rs
            else:
                raise AssertionError("unexpected op %s" % op)
        if isinstance(l, vhd_int) and isinstance(r, vhd_int):
            node.vhd = vhd_int()
        elif isinstance(l, (vhd_signed, vhd_int)) and isinstance(r, (vhd_signed, vhd_int)):
            node.vhd = vhd_signed(s)
        elif isinstance(l, (vhd_unsigned, vhd_int)) and isinstance(r, (vhd_unsigned, vhd_int)):
            node.vhd = vhd_unsigned(s)
        else:
            node.vhd = vhd_int()
        node.vhdOri = copy(node.vhd)




#     def multiBoolOp(self, node):
#         self.visitChildNodes(node)
#         for n in node.nodes:
#             n.vhd = vhd_boolean()
#         node.vhd = vhd_boolean()
#         node.vhdOri = copy(node.vhd)
#     visitAnd = visitOr = multiBoolOp


    def visit_BoolOp(self, node):
        self.generic_visit(node)
        for n in node.values:
            n.vhd = vhd_boolean()
        node.vhd = vhd_boolean()
        node.vhdOri = copy(node.vhd)



#     def visitIf(self, node):
#         if node.ignore:
#             return
#         self.visitChildNodes(node)
#         for test, suite in node.tests:
#             test.vhd = vhd_boolean()

    def visit_If(self, node):
        if node.ignore:
            return
        self.generic_visit(node)
        for test, suite in node.tests:
            test.vhd = vhd_boolean()
            
    def visit_IfExp(self, node):
        self.generic_visit(node)
        node.test.vhd = vhd_boolean()

#     def visitListComp(self, node):
#         pass # do nothing


    def visit_ListComp(self, node):
        pass # do nothing


    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)

#     def visitSlice(self, node):
#         self.visitChildNodes(node)
# ##         lower = 0
# ##         t = vhd_unsigned
# ##         if hasattr(node.expr, 'vhd'):
# ##             lower = node.expr.vhd.size
# ##             t = type(node.expr.vhd)
#         lower = node.expr.vhd.size
#         t = type(node.expr.vhd)
#         # node.expr.vhd = vhd_unsigned(node.expr.vhd.size)
#         if node.lower:
#             lower = self.getVal(node.lower)
#         upper = 0
#         if node.upper:
#             upper = self.getVal(node.upper)
#         if node.flags == 'OP_ASSIGN':
#             node.vhd = t(lower-upper)
#         else:
#             node.vhd = vhd_unsigned(lower-upper)
#         node.vhdOri = copy(node.vhd)


    def accessSlice(self, node):
        self.generic_visit(node)
        lower = node.value.vhd.size
        t = type(node.value.vhd)
        # node.expr.vhd = vhd_unsigned(node.expr.vhd.size)
        if node.slice.lower:
            lower = self.getVal(node.slice.lower)
        upper = 0
        if node.slice.upper:
            upper = self.getVal(node.slice.upper)
        if isinstance(node.ctx, ast.Store):
            node.vhd = t(lower-upper)
        else:
            node.vhd = vhd_unsigned(lower-upper)
        node.vhdOri = copy(node.vhd)


#     def visitSubscript(self, node):
#         self.visitChildNodes(node)
#         node.vhd = vhd_std_logic() # XXX default
#         o = node.expr.obj
#         if isinstance(o, list):
#             assert len(o)
#             node.vhd = inferVhdlObj(o[0])
#         elif isinstance(o, _Ram):
#             node.vhd = inferVhdlObj(o.elObj)
#         elif isinstance(o, _Rom):
#             node.vhd = vhd_int()
#         elif isinstance(o, intbv):
#             node.vhd = vhd_std_logic()
#         node.vhdOri = copy(node.vhd)


    def accessIndex(self, node):
        self.generic_visit(node)
        node.vhd = vhd_std_logic() # XXX default
        obj = node.value.obj
        if isinstance(obj, list):
            assert len(obj)
            node.vhd = inferVhdlObj(obj[0])
        elif isinstance(obj, _Ram):
            node.vhd = inferVhdlObj(obj.elObj)
        elif isinstance(obj, _Rom):
            node.vhd = vhd_int()
        elif isinstance(obj, intbv):
            node.vhd = vhd_std_logic()
        node.vhdOri = copy(node.vhd)


#     def unaryOp(self, node):
#         self.visit(node.expr)
#         node.vhd = copy(node.expr.vhd)
#         node.vhdOri = copy(node.vhd)

#     def visitNot(self, node):
#         self.visit(node.expr)
#         node.vhd = node.expr.vhd = vhd_boolean()


#     visitUnaryAdd = unaryOp
# ##     visitInvert = unaryOp
#     def visitInvert(self, node):
#         self.visit(node.expr)
#         node.vhd = copy(node.expr.vhd)
#         node.vhdOri = copy(node.vhd)
    
#     def visitUnarySub(self, node):
#         self.visit(node.expr)
#         node.vhd = node.expr.vhd
#         if isinstance(node.vhd, vhd_unsigned):
#             node.vhd = vhd_signed(node.vhd.size + 1)
#         elif isinstance(node.vhd, vhd_nat):
#             node.vhd = vhd_int()
#         node.vhdOri = copy(node.vhd)


    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        node.vhd = copy(node.operand.vhd)
        if isinstance(node.op, ast.Not):
            node.vhd = node.operand.vhd = vhd_boolean()
        elif isinstance(node.op, ast.USub):
            if isinstance(node.vhd, vhd_unsigned):
                node.vhd = vhd_signed(node.vhd.size+1)
            elif isinstance(node.vhd, vhd_nat):
                node.vhd = vhd_int()
        node.vhdOri = copy(node.vhd)
       

#     def visitWhile(self, node):
#         self.visitChildNodes(node)
#         node.test.vhd = vhd_boolean()

    def visit_While(self, node):
        self.generic_visit(node)
        node.test.vhd = vhd_boolean()


    

def _annotateTypes(genlist):
    for tree in genlist:
        if isinstance(tree, _UserVhdlCode):
            continue
        v = _AnnotateTypesVisitor(tree)
        v.visit(tree)



    

    
 
