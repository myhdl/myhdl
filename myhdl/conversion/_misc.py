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

""" myhdl toVerilog package.

"""
from __future__ import absolute_import


import ast

from myhdl import ConversionError
from myhdl._compat import PY2


class _error(object):
    FirstArgType = "first argument should be a classic function"
    ArgType = "leaf cell type error"
    NotSupported = "Not supported"
    TopLevelName = "Result of toVerilog call should be assigned to a top level name"
    SigMultipleDriven = "Signal has multiple drivers"
    UndefinedBitWidth = "Signal has undefined bit width"
    UndrivenSignal = "Signal is not driven"
    UnreadSignal = "Signal is driven but not read"
    UnusedPort = "Port is not used"
    OutputPortRead = "Output port is read internally"
    Requirement = "Requirement violation"
    UnboundLocal = "Local variable may be referenced before assignment"
    TypeMismatch = "Type mismatch with earlier assignment"
    NrBitsMismatch = "Nr of bits mismatch with earlier assignment"
    IntbvBitWidth = "intbv object should have a bit width"
    #IntbvSign = "intbv's that can have negative values are not yet supported"
    ModbvRange = "modbv object should have full bit vector range"
    TypeInfer = "Can't infer variable type"
    ReturnTypeMismatch = "Return type mismatch"
    ReturnNrBitsMismatch = "Returned nr of bits mismatch"
    ReturnIntbvBitWidth = "Returned intbv instance should have bit width"
    ReturnTypeInfer = "Can't infer return type"
    ShadowingSignal = "Port is not used or shadowed by internal signal"
    ShadowingVar = "Variable has same name as a hierarchical Signal"
    FreeVarTypeError = "Free variable should be a Signal or an int"
    ExtraArguments = "Extra positional or named arguments are not supported"
    UnsupportedYield = "Unsupported yield statement"
    UnsupportedListComp = \
        "Unsupported list comprehension form: should be [intbv()[n:] for i in range(m)]"
    ListElementAssign = \
        "Can't assign to list element; use slice assignment to change its value"
    NotASignal = "Non-local object should be a Signal"
    UnsupportedType = "Object type is not supported in this context"
    InconsistentType = "Signal elements should have the same base type"
    InconsistentBitWidth = "Signal elements should have the same bit width"
    UnsupportedFormatString = "Unsupported format string"
    FormatString = "Format string error"
    UnsupportedAttribute = "Unsupported attribute"
    PortInList = "Port in list is not supported"
    ListAsPort = "List of signals as a port is not supported"
    SignalInMultipleLists = "Signal in multiple list is not supported"


class _access(object):
    INPUT, OUTPUT, INOUT, UNKNOWN = range(4)


class _kind(object):
    NORMAL, DECLARATION, ALWAYS, INITIAL, ALWAYS_DECO, \
        ALWAYS_COMB, SIMPLE_ALWAYS_COMB, ALWAYS_SEQ, \
        TASK, REG \
        = range(10)


class _context(object):
    BOOLEAN, YIELD, PRINT, SIGNED, UNKNOWN = range(5)


class _ConversionMixin(object):

    #     def getLineNo(self, node):
    #         lineno = node.lineno
    #         if lineno is None:
    #             for n in node.getChildNodes():
    #                 if n.lineno is not None:
    #                     lineno = n.lineno
    #                     break
    #         lineno = lineno or 0
    #         return lineno

    def getLineNo(self, node):
        lineno = 0
        if isinstance(node, (ast.stmt, ast.expr)):
            lineno = node.lineno
        return lineno

    def getObj(self, node):
        if hasattr(node, 'obj'):
            return node.obj
        return None

    def getTarget(self, node):
        if hasattr(node, 'target'):
            return node.target
        return None

    def getKind(self, node):
        if hasattr(node, 'kind'):
            return node.kind
        return None

    def getEdge(self, node):
        if hasattr(node, 'edge'):
            return node.edge
        return None

    def getValue(self, node):
        if hasattr(node, 'value'):
            return node.value
        return None

    def getVal(self, node):
        expr = ast.Expression()
        expr.body = node
        expr.lineno = node.lineno
        expr.col_offset = node.col_offset
        c = compile(expr, '<string>', 'eval')
        val = eval(c, self.tree.symdict, self.tree.vardict)
        # val = eval(_unparse(node), self.tree.symdict, self.tree.vardict)
        return val

    def raiseError(self, node, kind, msg=""):
        lineno = self.getLineNo(node)
        info = "in file %s, line %s:\n    " % \
            (self.tree.sourcefile, self.tree.lineoffset + lineno)
        raise ConversionError(kind, msg, info)

    def require(self, node, test, msg=""):
        assert isinstance(node, ast.AST)
        if not test:
            self.raiseError(node, _error.Requirement, msg)

    def visitChildNodes(self, node, *args):
        for n in node.getChildNodes():
            self.visit(n, *args)

    def visitList(self, nodes):
        for n in nodes:
            self.visit(n)


def _LabelGenerator():
    i = 1
    while 1:
        yield "MYHDL%s" % i
        i += 1

_genLabel = _LabelGenerator()


class _Label(object):

    def __init__(self, name):
        self.name = next(_genLabel) + '_' + name
        self.isActive = False

    def __str__(self):
        return str(self.name)

# this can be made more sophisticated to deal with existing suffixes
# also, may require reset facility


class _UniqueSuffixGenerator(object):

    def __init__(self):
        self.i = 0

    def reset(self):
        self.i = 0

    def next(self):
        self.i += 1
        return "_%s" % self.i

_genUniqueSuffix = _UniqueSuffixGenerator()


# check if expression is constant
def _isConstant(tree, symdict):
    v = _namesVisitor()
    v.visit(tree)
    for name in v.names:
        if name not in symdict:
            return False
        if not isinstance(symdict[name], int):
            return False
    return True


class _namesVisitor(ast.NodeVisitor):

    def __init__(self):
        self.names = []

    def visit_Name(self, node):
        self.names.append(node.id)


def _get_argnames(node):
    if PY2:
        return [arg.id for arg in node.args.args]
    else:
        return [arg.arg for arg in node.args.args]
