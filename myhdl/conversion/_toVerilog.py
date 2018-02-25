#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2012 Jan Decaluwe
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
from __future__ import absolute_import
from __future__ import print_function


import sys
import math
import os
import textwrap

import inspect
from datetime import datetime
import ast
import string

from types import GeneratorType
from myhdl._compat import StringIO
import warnings

import myhdl
from myhdl import *
from myhdl._compat import integer_types, class_types, PY2
from myhdl import ToVerilogError, ToVerilogWarning
from myhdl._extractHierarchy import (_HierExtr, _isMem, _getMemInfo,
                                     _UserVerilogCode, _userCodeMap)

from myhdl._instance import _Instantiator
from myhdl.conversion._misc import (_error, _kind, _context,
                                    _ConversionMixin, _Label, _genUniqueSuffix, _isConstant)
from myhdl.conversion._analyze import (_analyzeSigs, _analyzeGens, _analyzeTopFunc,
                                       _Ram, _Rom)
from myhdl._Signal import _Signal
from myhdl._ShadowSignal import _TristateSignal, _TristateDriver

from myhdl._block import _Block
from myhdl._getHierarchy import _getHierarchy

_converting = 0
_profileFunc = None


def _checkArgs(arglist):
    for arg in arglist:
        if not isinstance(arg, (GeneratorType, _Instantiator, _UserVerilogCode)):
            raise ToVerilogError(_error.ArgType, arg)


def _flatten(*args):
    arglist = []
    for arg in args:
        if isinstance(arg, _Block):
            if arg.verilog_code is not None:
                arglist.append(arg.verilog_code)
                continue
            else:
                arg = arg.subs
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
    doc = inspect.cleandoc(doc)
    pre = '\n' + indent + '// '
    doc = '// ' + doc
    doc = doc.replace('\n', pre)
    return doc


class _ToVerilogConvertor(object):

    __slots__ = ("name",
                 "directory",
                 "timescale",
                 "standard",
                 "prefer_blocking_assignments",
                 "radix",
                 "header",
                 "no_myhdl_header",
                 "no_testbench",
                 "portmap",
                 "trace",
                 "initial_values"
                 )

    def __init__(self):
        self.name = None
        self.directory = None
        self.timescale = "1ns/10ps"
        self.standard = '2001'
        self.prefer_blocking_assignments = True
        self.radix = ''
        self.header = ''
        self.no_myhdl_header = False
        self.no_testbench = False
        self.trace = False
        self.initial_values = False

    def __call__(self, func, *args, **kwargs):
        global _converting
        if _converting:
            return func(*args, **kwargs)  # skip
        else:
            # clean start
            sys.setprofile(None)
        from myhdl import _traceSignals
        if _traceSignals._tracing:
            raise ToVerilogError("Cannot use toVerilog while tracing signals")
        if not isinstance(func, _Block):
            if not callable(func):
                raise ToVerilogError(_error.FirstArgType, "got %s" % type(func))

        _converting = 1
        if self.name is None:
            name = func.__name__
            if isinstance(func, _Block):
                name = func.func.__name__
        else:
            name = str(self.name)

        if isinstance(func, _Block):
            try:
                h = _getHierarchy(name, func)
            finally:
                _converting = 0
        else:
            warnings.warn(
                "\n    toVerilog(): Deprecated usage: See http://dev.myhdl.org/meps/mep-114.html", stacklevel=2)
            try:
                h = _HierExtr(name, func, *args, **kwargs)
            finally:
                _converting = 0

        if self.directory is None:
            directory = ''
        else:
            directory = self.directory

        vfilename = name + ".v"
        vpath = os.path.join(directory, vfilename)
        vfile = open(vpath, 'w')

        ### initialize properly ###
        _genUniqueSuffix.reset()

        arglist = _flatten(h.top)
        # print h.top
        _checkArgs(arglist)
        genlist = _analyzeGens(arglist, h.absnames)
        siglist, memlist = _analyzeSigs(h.hierarchy)
        _annotateTypes(genlist)

        # infer interface
        if isinstance(func, _Block):
            # infer interface after signals have been analyzed
            func._inferInterface()
            intf = func
        else:
            intf = _analyzeTopFunc(func, *args, **kwargs)

        intf.name = name

        doc = _makeDoc(inspect.getdoc(func))

        self._convert_filter(h, intf, siglist, memlist, genlist)

        _writeFileHeader(vfile, vpath, self.timescale)
        _writeModuleHeader(vfile, intf, doc)
        _writeSigDecls(vfile, intf, siglist, memlist)
        _convertGens(genlist, vfile)
        _writeModuleFooter(vfile)

        vfile.close()

        # don't write testbench if module has no ports
        if len(intf.argnames) > 0 and not toVerilog.no_testbench:
            tbpath = os.path.join(directory, "tb_" + vfilename)
            tbfile = open(tbpath, 'w')
            _writeTestBench(tbfile, intf, self.trace)
            tbfile.close()

        # build portmap for cosimulation
        portmap = {}
        for n, s in intf.argdict.items():
            if hasattr(s, 'driver'):
                portmap[n] = s.driver()
            else:
                portmap[n] = s
        self.portmap = portmap

        ### clean-up properly ###
        self._cleanup(siglist, memlist)

        return h.top

    def _cleanup(self, siglist, memlist):
        # clean up signals
        for sig in siglist:
            sig._clear()
        for mem in memlist:
            mem.name = None
            for s in mem.mem:
                s._clear()

        # clean up attributes
        self.name = None
        self.standard = '2001'
        self.prefer_blocking_assignments = True
        self.radix = ''
        self.header = ""
        self.no_myhdl_header = False
        self.no_testbench = False
        self.trace = False

    def _convert_filter(self, h, intf, siglist, memlist, genlist):
        # intended to be a entry point for other uses:
        #  code checking, optimizations, etc
        pass


toVerilog = _ToVerilogConvertor()

myhdl_header = """\
// File: $filename
// Generated by MyHDL $version
// Date: $date
"""


def _writeFileHeader(f, fn, ts):
    vars = dict(filename=fn,
                version=myhdl.__version__,
                date=datetime.today().ctime()
                )
    if not toVerilog.no_myhdl_header:
        print(string.Template(myhdl_header).substitute(vars), file=f)
    if toVerilog.header:
        print(string.Template(toVerilog.header).substitute(vars), file=f)
    print(file=f)
    print("`timescale %s" % ts, file=f)
    print(file=f)


def _writeModuleHeader(f, intf, doc):
    print("module %s (" % intf.name, file=f)
    b = StringIO()
    for portname in intf.argnames:
        print("    %s," % portname, file=b)
    print(b.getvalue()[:-2], file=f)
    b.close()
    print(");", file=f)
    print(doc, file=f)
    print(file=f)
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
                if not isinstance(s, _TristateSignal):
                    warnings.warn("%s: %s" % (_error.OutputPortRead, portname),
                                  category=ToVerilogWarning
                                  )
            if isinstance(s, _TristateSignal):
                print("inout %s%s%s;" % (p, r, portname), file=f)
            else:
                print("output %s%s%s;" % (p, r, portname), file=f)
            if s._driven == 'reg':
                print("reg %s%s%s;" % (p, r, portname), file=f)
            else:
                print("wire %s%s%s;" % (p, r, portname), file=f)
        else:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedPort, portname),
                              category=ToVerilogWarning
                              )
            print("input %s%s%s;" % (p, r, portname), file=f)
    print(file=f)


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
            if not s._read and not isinstance(s, _TristateDriver):
                warnings.warn("%s: %s" % (_error.UnreadSignal, s._name),
                              category=ToVerilogWarning
                              )
            k = 'wire'
            if s._driven == 'reg':
                k = 'reg'
            # the following line implements initial value assignments
            # don't initial value "wire", inital assignment to a wire
            # equates to a continuous assignment [reference]
            if not toVerilog.initial_values or k == 'wire':
                print("%s %s%s%s;" % (k, p, r, s._name), file=f)
            else:
                if isinstance(s._init, myhdl._enum.EnumItemType):
                    print("%s %s%s%s = %s;" %
                          (k, p, r, s._name, s._init._toVerilog()), file=f)
                else:
                    print("%s %s%s%s = %s;" %
                          (k, p, r, s._name, _intRepr(s._init)), file=f)
        elif s._read:
            # the original exception
            # raise ToVerilogError(_error.UndrivenSignal, s._name)
            # changed to a warning and a continuous assignment to a wire
            warnings.warn("%s: %s" % (_error.UndrivenSignal, s._name),
                          category=ToVerilogWarning
                          )
            constwires.append(s)
            print("wire %s%s;" % (r, s._name), file=f)
    # print(file=f)
    for m in memlist:
        if not m._used:
            continue
        # infer attributes for the case of named signals in a list
        for i, s in enumerate(m.mem):
            if not m._driven and s._driven:
                m._driven = s._driven
            if not m._read and s._read:
                m._read = s._read
        if not m._driven and not m._read:
            continue
        r = _getRangeString(m.elObj)
        p = _getSignString(m.elObj)
        k = 'wire'
        initial_assignments = None
        if m._driven:
            k = m._driven

            if toVerilog.initial_values and not k == 'wire':
                if all([each._init == m.mem[0]._init for each in m.mem]):

                    initialize_block_name = ('INITIALIZE_' + m.name).upper()
                    _initial_assignments = (
                        '''
                        initial begin: %s
                            integer i;
                            for(i=0; i<%d; i=i+1) begin
                                %s[i] = %s;
                            end
                        end
                        ''' % (initialize_block_name, len(m.mem), m.name,
                               _intRepr(m.mem[0]._init)))

                    initial_assignments = (
                        textwrap.dedent(_initial_assignments))

                else:
                    val_assignments = '\n'.join(
                        ['    %s[%d] <= %s;' %
                         (m.name, n, _intRepr(each._init))
                         for n, each in enumerate(m.mem)])
                    initial_assignments = (
                        'initial begin\n' + val_assignments + '\nend')

        print("%s %s%s%s [0:%s-1];" % (k, p, r, m.name, m.depth),
              file=f)

        if initial_assignments is not None:
            print(initial_assignments, file=f)

    print(file=f)
    for s in constwires:
        if s._type in (bool, intbv):
            c = int(s.val)
        else:
            raise ToVerilogError("Unexpected type for constant signal", s._name)
        c_len = s._nrbits
        c_str = "%s" % c
        print("assign %s = %s'd%s;" % (s._name, c_len, c_str), file=f)
    # print(file=f)
    # shadow signal assignments
    for s in siglist:
        if hasattr(s, 'toVerilog') and s._driven:
            print(s.toVerilog(), file=f)
    print(file=f)


def _writeModuleFooter(f):
    print("endmodule", file=f)


def _writeTestBench(f, intf, trace=False):
    print("module tb_%s;" % intf.name, file=f)
    print(file=f)
    fr = StringIO()
    to = StringIO()
    pm = StringIO()
    for portname in intf.argnames:
        s = intf.argdict[portname]
        r = _getRangeString(s)
        if s._driven:
            print("wire %s%s;" % (r, portname), file=f)
            print("        %s," % portname, file=to)
        else:
            print("reg %s%s;" % (r, portname), file=f)
            print("        %s," % portname, file=fr)
        print("    %s," % portname, file=pm)
    print(file=f)
    print("initial begin", file=f)
    if trace:
        print('    $dumpfile("%s.vcd");' % intf.name, file=f)
        print('    $dumpvars(0, dut);', file=f)
    if fr.getvalue():
        print("    $from_myhdl(", file=f)
        print(fr.getvalue()[:-2], file=f)
        print("    );", file=f)
    if to.getvalue():
        print("    $to_myhdl(", file=f)
        print(to.getvalue()[:-2], file=f)
        print("    );", file=f)
    print("end", file=f)
    print(file=f)
    print("%s dut(" % intf.name, file=f)
    print(pm.getvalue()[:-2], file=f)
    print(");", file=f)
    print(file=f)
    print("endmodule", file=f)


def _getRangeString(s):
    if s._type is bool:
        return ''
    elif s._nrbits is not None:
        nrbits = s._nrbits
        return "[%s:0] " % (nrbits - 1)
    else:
        raise AssertionError


def _getSignString(s):
    if s._min is not None and s._min < 0:
        return "signed "
    else:
        return ''

def _intRepr(n, radix=''):
    # write size for large integers (beyond 32 bits signed)
    # with some safety margin
    # XXX signed indication 's' ???
    p = abs(n)
    size = ''
    num = str(p).rstrip('L')
    if radix == "hex" or p >= 2**30:
        radix = "'h"
        num = hex(p)[2:].rstrip('L')
    if p >= 2**30:
        size = int(math.ceil(math.log(p+1,2))) + 1  # sign bit!
#            if not radix:
#                radix = "'d"
    r = "%s%s%s" % (size, radix, num)
    if n < 0: # add brackets and sign on negative numbers
        r = "(-%s)" % r
    return r

def _convertGens(genlist, vfile):
    blockBuf = StringIO()
    funcBuf = StringIO()
    for tree in genlist:
        if isinstance(tree, _UserVerilogCode):
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
        elif tree.kind == _kind.ALWAYS_SEQ:
            Visitor = _ConvertAlwaysSeqVisitor
        else:  # ALWAYS_COMB
            Visitor = _ConvertAlwaysCombVisitor
        v = Visitor(tree, blockBuf, funcBuf)
        v.visit(tree)
    vfile.write(funcBuf.getvalue())
    funcBuf.close()
    vfile.write(blockBuf.getvalue())
    blockBuf.close()


opmap = {
    ast.Add: '+',
    ast.Sub: '-',
    ast.Mult: '*',
    ast.Div: '/',
    ast.Mod: '%',
    ast.Pow: '**',
    ast.LShift: '<<',
    ast.RShift: '>>>',
    ast.BitOr: '|',
    ast.BitAnd: '&',
    ast.BitXor: '^',
    ast.FloorDiv: '/',
    ast.Invert: '~',
    ast.Not: '!',
    ast.UAdd: '+',
    ast.USub: '-',
    ast.Eq: '==',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.NotEq: '!=',
    ast.And: '&&',
    ast.Or: '||',
}

nameconstant_map = {
    True: "1'b1",
    False: "1'b0",
    None: "'bz"
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
            (self.tree.sourcefile, self.tree.lineoffset + lineno)
        raise ToVerilogError(kind, msg, info)

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

    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def IntRepr(self, n, radix=''):
        return _intRepr(n, radix)

    def writeDeclaration(self, obj, name, dir):
        if dir:
            dir = dir + ' '
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

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and self.context == _context.PRINT:
            self.visit(node.left)
            self.write(", ")
            self.visit(node.right)
        else:
            if isinstance(node.op, ast.RShift):
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
        if isinstance(node, ast.Name):
            o = node.obj
            if isinstance(o, (_Signal, intbv)) and o.min is not None and o.min < 0:
                self.raiseError(node, _error.NotSupported,
                                "negative intbv with operator %s" % op)

    def visit_BoolOp(self, node):
        self.write("(")
        self.visit(node.values[0])
        for n in node.values[1:]:
            self.write(" %s " % opmap[type(node.op)])
            self.visit(n)
        self.write(")")

    def visit_UnaryOp(self, node):
        self.write("(%s" % opmap[type(node.op)])
        self.visit(node.operand)
        self.write(")")

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
        if isinstance(node.value, ast.Subscript):
            self.setAttr(node)
            return

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
                if i == len(rom) - 1:
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
                self.write("%s;" % s)
            self.dedent()
            self.writeline()
            self.write("endcase")
            return
        elif isinstance(node.value, ast.ListComp):
            # skip list comprehension assigns for now
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

    def visit_AugAssign(self, node, *args):
        # XXX apparently no signed context required for augmented assigns
        self.visit(node.target)
        self.write(" = ")
        self.visit(node.target)
        self.write(" %s " % opmap[type(node.op)])
        self.visit(node.value)
        self.write(";")

    def visit_Break(self, node,):
        self.write("disable %s;" % self.labelStack[-2])

    def visit_Call(self, node):
        self.context = None
        fn = node.func
        # assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)

        if f is print:
            self.visit_Print(node)
            return

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
            self.write(repr(val))
            return
        elif f is now:
            self.write("$time")
            return
        elif f is ord:
            opening, closing = '', ''
            node.args[0].s = str(ord(node.args[0].s))
        elif f in integer_types:
            opening, closing = '', ''
            # convert number argument to integer
            if isinstance(node.args[0], ast.Num):
                node.args[0].n = int(node.args[0].n)
        elif f in (intbv, modbv):
            self.visit(node.args[0])
            return
        elif f == intbv.signed:  # note equality comparison
            # comes from a getattr
            opening, closing = '', ''
            if not fn.value.signed:
                opening, closing = "$signed(", ")"
            self.write(opening)
            self.visit(fn.value)
            self.write(closing)
        elif (type(f) in class_types) and issubclass(f, Exception):
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

    def visit_Num(self, node):
        if self.context == _context.PRINT:
            self.write('"%s"' % node.n)
        else:
            self.write(self.IntRepr(node.n))

    def visit_Str(self, node):
        s = node.s
        if self.context == _context.PRINT:
            self.write('"%s"' % s)
        elif len(s) == s.count('0') + s.count('1'):
            self.write("%s'b%s" % (len(s), s))
        else:
            self.write(s)

    def visit_Continue(self, node):
        self.write("disable %s;" % self.labelStack[-1])

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
        self.visit(node.test)
        self.write(' ? ')
        self.visit(node.body)
        self.write(' : ')
        self.visit(node.orelse)

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
        else:  # downrange
            cmp = '>='
            op = '-'
            oneoff = '-1'
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

    def visit_FunctionDef(self, node):
        raise AssertionError("To be implemented in subclass")

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
        caseType = "case"
        if isinstance(node.caseItem, EnumItemType):
            if node.caseItem._type._encoding in ('one_hot', 'one_cold'):
                caseType = "casez"
        self.write("%s (" % caseType)
        self.visit(var)
        self.write(")")
        self.indent()
        for test, suite in node.tests:
            self.writeline()
            item = test.case[1]
            if isinstance(item, EnumItemType):
                self.write(item._toVerilog(dontcare=True))
            else:
                self.write(self.IntRepr(item, radix='hex'))
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

    def visit_ListComp(self, node):
        pass  # do nothing

    def visit_NameConstant(self, node):
        self.write(nameconstant_map[node.obj])

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setName(node)
        else:
            self.getName(node)

    def setName(self, node):
        self.write(node.id)

    def getName(self, node):
        n = node.id
        if PY2 and n in ('True', 'False', 'None'):
            self.visit_NameConstant(node)
            return

        addSignBit = False
        isMixedExpr = (not node.signed) and (self.context == _context.SIGNED)
        if n in self.tree.vardict:
            addSignBit = isMixedExpr
            s = n
        elif n in self.tree.argnames:
            assert n in self.tree.symdict
            addSignBit = isMixedExpr
            s = n
        elif n in self.tree.symdict:
            obj = self.tree.symdict[n]
            if isinstance(obj, bool):
                s = "1'b%s" % int(obj)
            elif isinstance(obj, integer_types):
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
            elif (type(obj) in class_types) and issubclass(obj, Exception):
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

    def visit_Pass(self, node):
        self.write("// pass")

    def visit_Print(self, node):
        argnr = 0
        for s in node.format:
            if isinstance(s, str):
                self.write('$write("%s");' % s)
            else:
                a = node.args[argnr]
                argnr += 1
                obj = a.obj
                if s.conv is int or isinstance(obj, int):
                    fs = "%0d"
                else:
                    fs = "%h"
                self.context = _context.PRINT
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
                    print (type(obj), type(a))
                    self.write('$write("%s", ' % fs)
                    self.visit(a)
                    self.write(');')
                self.context = _context.UNKNOWN
            self.writeline()
        self.write('$write("\\n");')

    def visit_Raise(self, node):
        self.write("$finish;")

    def visit_Return(self, node):
        self.write("disable %s;" % self.returnLabel)

    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)

    def accessSlice(self, node):
        if isinstance(node.value, ast.Call) and \
           node.value.func.obj in (intbv, modbv) and \
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

    def visit_stmt(self, body):
        for stmt in body:
            self.writeline()
            self.visit(stmt)
            # ugly hack to detect an orphan "task" call
            if isinstance(stmt, ast.Call) and hasattr(stmt, 'tree'):
                self.write(';')

    def visit_Tuple(self, node):
        assert self.context != None
        sep = ", "
        tpl = node.elts
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(sep)
            self.visit(elt)

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

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
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

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
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

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.write("assign ")
            self.visit(node.value)
        else:
            self.getAttr(node)

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.visit_stmt(node.body)
        self.writeline(2)


class _ConvertAlwaysDecoVisitor(_ConvertVisitor):

    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.writeAlwaysHeader()
        self.writeDeclarations()
        self.visit_stmt(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)


def _convertInitVal(reg, init):
    if isinstance(reg, _Signal):
        tipe = reg._type
    else:
        assert isinstance(reg, intbv)
        tipe = intbv
    if tipe is bool:
        v = '1' if init else '0'
    elif tipe is intbv:
        init = int(init) # int representation
        v = "%s" % init if init is not None else "'bz"
    else:
        assert isinstance(init, EnumItemType)
        v = init._toVerilog()
    return v


class _ConvertAlwaysSeqVisitor(_ConvertVisitor):

    def __init__(self, tree, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, tree, blockBuf)
        self.funcBuf = funcBuf

    def visit_FunctionDef(self, node):
        self.writeDoc(node)
        self.writeAlwaysHeader()
        self.writeDeclarations()
        reset = self.tree.reset
        sigregs = self.tree.sigregs
        varregs = self.tree.varregs
        if reset is not None:
            self.writeline()
            self.write("if (%s == %s) begin" % (reset, int(reset.active)))
            self.indent()
            for s in sigregs:
                self.writeline()
                self.write("%s <= %s;" % (s, _convertInitVal(s, s._init)))
            for v in varregs:
                n, reg, init = v
                self.writeline()
                self.write("%s = %s;" % (n, _convertInitVal(reg, init)))
            self.dedent()
            self.writeline()
            self.write("end")
            self.writeline()
            self.write("else begin")
            self.indent()
        self.visit_stmt(node.body)
        self.dedent()
        if reset is not None:
            self.writeline()
            self.write("end")
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


def _maybeNegative(obj):
    if hasattr(obj, '_min') and (obj._min is not None) and (obj._min < 0):
        return True
    if isinstance(obj, integer_types) and obj < 0:
        return True
    return False


class _AnnotateTypesVisitor(ast.NodeVisitor, _ConversionMixin):

    def __init__(self, tree):
        self.tree = tree

    def visit_FunctionDef(self, node):
        # don't visit arguments and decorators
        for stmt in node.body:
            self.visit(stmt)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        node.signed = node.left.signed or node.right.signed
        # special treatement of subtraction unless in a top-level rhs
        if isinstance(node.op, ast.Sub) and not hasattr(node, 'isRhs'):
            node.signed = True

    def visit_BoolOp(self, node):
        for n in node.values:
            self.visit(n)
        node.signed = False

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        node.signed = node.operand.signed
        if isinstance(node.op, ast.USub):
            node.obj = int(-1)
            if isinstance(node.operand, ast.Num):
                node.signed = True

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setAttr(node)
        else:
            self.getAttr(node)

    def setAttr(self, node):
        self.visit(node.value)

    def getAttr(self, node):
        node.signed = False
        self.visit(node.value)

    def visit_Call(self, node):
        self.generic_visit(node)
        f = self.getObj(node.func)
        node.signed = False
        # suprize: identity comparison on unbound methods doesn't work in python 2.5??
        if f == intbv.signed:
            node.signed = True
        elif hasattr(node, 'tree'):
            v = _AnnotateTypesVisitor(node.tree)
            v.visit(node.tree)
            node.signed = _maybeNegative(node.tree.returnObj)

    def visit_Compare(self, node):
        node.signed = False
        # for n in ast.iter_child_nodes(node):
        for n in [node.left] + node.comparators:
            self.visit(n)
            if n.signed:
                node.signed = True

    def visit_If(self, node):
        if node.ignore:
            return
        self.generic_visit(node)

    def visit_Num(self, node):
        node.signed = False

    def visit_Str(self, node):
        node.signed = False

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setName(node)
        else:
            self.getName(node)

    def setName(self, node):
        pass

    def getName(self, node):
        node.signed = _maybeNegative(node.obj)

    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)

    def accessSlice(self, node):
        node.signed = False
        self.generic_visit(node)

    def accessIndex(self, node):
        node.signed = _maybeNegative(node.obj)
        self.generic_visit(node)

    def visit_Tuple(self, node):
        node.signed = False
        self.generic_visit(node)


def _annotateTypes(genlist):
    for tree in genlist:
        if isinstance(tree, _UserVerilogCode):
            continue
        v = _AnnotateTypesVisitor(tree)
        v.visit(tree)
