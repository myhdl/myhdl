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

""" myhdl toVerilog package.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import inspect
from compiler import ast as astNode

import myhdl
from myhdl import *
from myhdl import ToVerilogError
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
_error.FreeVarTypeError = "Free variable should be a Signal or an int"


_access = enum("INPUT", "OUTPUT", "INOUT", "UNKNOWN")
_kind = enum("NORMAL", "DECLARATION", "ALWAYS", "INITIAL", "ALWAYS_COMB")
_context = enum("BOOLEAN", "YIELD", "PRINT", "UNKNOWN")

    
class _ToVerilogMixin(object):
    
    def getLineNo(self, node):
        lineno = node.lineno
        if lineno is None:
            for n in node.getChildNodes():
                if n.lineno is not None:
                    lineno = n.lineno
                    break
        lineno = lineno or 0
        return lineno
    
    def getObj(self, node):
        if hasattr(node, 'obj'):
            return node.obj
        return None

    def getKind(self, node):
        if hasattr(node, 'kind'):
            return node.kind
        return None

    def getVal(self, node):
        val = eval(_unparse(node), self.ast.symdict)
        return val
    
    def raiseError(self, node, kind, msg=""):
        lineno = self.getLineNo(node)
        info = "in file %s, line %s:\n    " % \
              (self.ast.sourcefile, self.ast.lineoffset+lineno)
        raise ToVerilogError(kind, msg, info)

    def require(self, node, test, msg=""):
        assert isinstance(node, astNode.Node)
        if not test:
            self.raiseError(node, _error.Requirement, msg)

    def visitChildNodes(self, node, *args):
        for n in node.getChildNodes():
            self.visit(n, *args)
            

def _LabelGenerator():
    i = 1
    while 1:
        yield "_MYHDL%s" % i
        i += 1
        
_genLabel = _LabelGenerator()

class _Label(object):
    def __init__(self, name):
        self.name = _genLabel.next() + '_' + name
        self.isActive = False
    def __str__(self):
        return str(self.name)
