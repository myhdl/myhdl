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


import inspect
import compiler
from compiler import ast as astNode
import ast

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl._util import _flatten
from myhdl._unparse import _unparse

class _error:
    pass
_error.FirstArgType = "first argument should be a classic function"
_error.ArgType = "leaf cell type error"
_error.NotSupported = "Not supported"
_error.TopLevelName = "Result of toVerilog call should be assigned to a top level name"
_error.SigMultipleDriven = "Signal has multiple drivers"
_error.UndefinedBitWidth = "Signal has undefined bit width"
_error.UndrivenSignal = "Signal is not driven"
_error.UnreadSignal = "Signal is driven but not read"
_error.UnusedPort = "Port is not used"
_error.OutputPortRead = "Output port is read internally"
_error.Requirement = "Requirement violation"
_error.UnboundLocal = "Local variable may be referenced before assignment"
_error.TypeMismatch = "Type mismatch with earlier assignment"
_error.NrBitsMismatch = "Nr of bits mismatch with earlier assignment"
_error.IntbvBitWidth = "intbv should have bit width"
_error.IntbvSign = "intbv's that can have negative values are not yet supported"
_error.TypeInfer = "Can't infer variable type"
_error.ReturnTypeMismatch = "Return type mismatch"
_error.ReturnNrBitsMismatch = "Returned nr of bits mismatch"
_error.ReturnIntbvBitWidth = "Returned intbv instance should have bit width"
_error.ReturnTypeInfer = "Can't infer return type"
_error.ShadowingSignal = "Port is shadowed by internal signal"
_error.ShadowingVar = "Variable has same name as a hierarchical Signal"
_error.FreeVarTypeError = "Free variable should be a Signal or an int"
_error.ExtraArguments = "Extra positional or named arguments are not supported"
_error.UnsupportedYield = "Unsupported yield statement"
_error.UnsupportedListComp = \
    "Unsupported list comprehension form: should be [intbv()[n:] for i in range(m)]"
_error.ListElementAssign = \
     "Can't assign to list element; use slice assignment to change its value"
_error.NotASignal = "Non-local object should be a Signal"
_error.UnsupportedType = "Object type is not supported in this context"
_error.InconsistentType = "Signal elements should have the same base type"
_error.InconsistentBitWidth = "Signal elements should have the same bit width"
_error.UnsupportedFormatString = "Unsupported format string"
_error.FormatString = "Format string error"
_error.UnsupportedAttribute = "Unsupported attribute"
_error.PortInList = "Port in list is not supported"
_error.SignalInMultipleLists = "Signal in multiple list is not supported"


_access = enum("INPUT", "OUTPUT", "INOUT", "UNKNOWN")
_kind = enum("NORMAL", "DECLARATION", "ALWAYS", "INITIAL", "ALWAYS_COMB", "SIMPLE_ALWAYS_COMB", "ALWAYS_DECO", "TASK", "REG")
_context = enum("BOOLEAN", "YIELD", "PRINT" ,"SIGNED", "UNKNOWN")

    
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
              (self.tree.sourcefile, self.tree.lineoffset+lineno)
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
        self.name = _genLabel.next() + '_' + name
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
