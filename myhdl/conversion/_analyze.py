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

""" MyHDL conversion analysis module.

"""


import inspect
# import compiler
# from compiler import ast as astNode
from types import GeneratorType, FunctionType, ClassType, MethodType
from cStringIO import StringIO
import re
import warnings
import ast
import __builtin__

import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl._unparse import _unparse
from myhdl._cell_deref import _cell_deref
from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl._delay import delay
from myhdl.conversion._misc import (_error, _access, _kind, _context,
                                    _ConversionMixin, _Label, _genUniqueSuffix)
from myhdl._extractHierarchy import _isMem, _UserCode
from myhdl._Signal import _WaiterList
from myhdl._util import _isTupleOfInts, _dedent

myhdlObjects = myhdl.__dict__.values()
builtinObjects = __builtin__.__dict__.values()

_enumTypeSet = set()


def _makeName(n, prefixes):
    if len(prefixes) > 1:
#        name = '_' + '_'.join(prefixes[1:]) + '_' + n
        name = '_'.join(prefixes[1:]) + '_' + n
    else:
        name = n
    if '[' in name or ']' in name:
        name = "\\" + name + ' '
##     print prefixes
##     print name
    return name

def _makeAST(f):
    s = inspect.getsource(f)
    s = _dedent(s)
    return ast.parse(s)
                     
def _analyzeSigs(hierarchy, hdl='Verilog'):
    curlevel = 0
    siglist = []
    memlist = []
    prefixes = []
    open, close = '[', ']'
    if hdl == 'VHDL':
        open, close = '(', ')'
    
    for inst in hierarchy:
        level = inst.level
        name = inst.name
        sigdict = inst.sigdict
        memdict = inst.memdict
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta == -1:
            prefixes.append(name)
        else:
            prefixes = prefixes[:curlevel-1]
            prefixes.append(name)
        assert prefixes[-1] == name
        for n, s in sigdict.items():
            if s._name is not None:
                continue
            s._name = _makeName(n, prefixes)
            if not s._nrbits:
                raise ConversionError(_error.UndefinedBitWidth, s._name)
            siglist.append(s)
        # list of signals
        for n, m in memdict.items():
            if m.name is not None:
                continue
            m.name = _makeName(n, prefixes)
            memlist.append(m)

    # handle the case where a named signal appears in a list also by giving
    # priority to the list and marking the signals as unused
    for m in memlist:
        if not m._used:
            continue
        m._driven = 'reg'
        for i, s in enumerate(m.mem):
            s._name = "%s%s%s%s" % (m.name, open, i, close)
            s._used = False
            if s._inList:
                raise ConversionError(_error.SignalInMultipleLists, s._name)
            s._inList = True
            if not s._nrbits:
                raise ConversionError(_error.UndefinedBitWidth, s._name)
            if type(s.val) != type(m.elObj.val):
                raise ConversionError(_error.InconsistentType, s._name)
            if s._nrbits != m.elObj._nrbits:
                raise ConversionError(_error.InconsistentBitWidth, s._name)
            
    return siglist, memlist

        

def _analyzeGens(top, absnames):
    genlist = []
    for g in top:
        if isinstance(g, _UserCode):
            tree = g
        elif isinstance(g, (_AlwaysComb, _Always)):
            f = g.func
            s = inspect.getsource(f)
            s = _dedent(s)
            tree = ast.parse(s)
            tree.sourcefile = inspect.getsourcefile(f)
            tree.lineoffset = inspect.getsourcelines(f)[1]-1
            tree.symdict = f.func_globals.copy()
            tree.callstack = []
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    if isinstance(g, _AlwaysComb):
                        # print type(obj)
                        assert isinstance(obj, (int, long, Signal)) or \
                               _isMem(obj) or _isTupleOfInts(obj)
                    tree.symdict[n] = obj
            tree.name = absnames.get(id(g), str(_Label("BLOCK"))).upper()
            v = _FirstPassVisitor(tree)
            v.visit(tree)
            if isinstance(g, _AlwaysComb):
                v = _AnalyzeAlwaysCombVisitor(tree, g.senslist)
            else:
                v = _AnalyzeAlwaysDecoVisitor(tree, g.senslist)
            v.visit(tree)
        else: # @instance
            f = g.gen.gi_frame
            s = inspect.getsource(f)
            s = _dedent(s)
            tree = ast.parse(s)
            tree.sourcefile = inspect.getsourcefile(f)
            tree.lineoffset = inspect.getsourcelines(f)[1]-1
            tree.symdict = f.f_globals.copy()
            tree.symdict.update(f.f_locals)
            tree.callstack = []
            tree.name = absnames.get(id(g), str(_Label("BLOCK"))).upper()
            v = _FirstPassVisitor(tree)
            v.visit(tree)
            v = _AnalyzeBlockVisitor(tree)
            v.visit(tree)
        genlist.append(tree)
    return genlist


class _FirstPassVisitor(ast.NodeVisitor, _ConversionMixin):

    """First pass visitor.
    
    Prune unsupported contructs, and add some useful attributes.

    """
    
    def __init__(self, tree):
        self.tree = tree
        self.toplevel = True
        
    def visit_Tuple(self, node):
        if isinstance(node.ctx, ast.Store):
            self.raiseError(node, _error.NotSupported, "tuple assignment")

    def visit_Repr(self, node):
        self.raiseError(node, _error.NotSupported, "backquote")

    def visit_ClassDef(self, node):
        self.raiseError(node, _error.NotSupported, "class statement")

    def visit_Dict(self, node):
        self.raiseError(node, _error.NotSupported, "dictionary")

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Div):
            self.raiseError(node, _error.NotSupported, "true division - consider '//'")

    def visit_Ellipsis(self, node):
        self.raiseError(node, _error.NotSupported, "ellipsis")

    def visit_Exec(self, node):
        self.raiseError(node, _error.NotSupported, "exec statement")

    def visitExpression(self, node, *args):
        self.raiseError(node, _error.NotSupported, "Expression node")

    def visit_ImportFrom(self, node):
        self.raiseError(node, _error.NotSupported, "from statement")

    def visit_Global(self, node):
        self.raiseError(node, _error.NotSupported, "global statement")

    def visit_Import(self, node):
        self.raiseError(node, _error.NotSupported, "import statement")

    def visit_Lambda(self, node):
        self.raiseError(node, _error.NotSupported, "lambda statement")

    def visit_ListComp(self, node):
        if len(node.generators) > 1:
            self.raiseError(node, _error.NotSupported, "multiple for statements in list comprehension")
        if node.generators[0].ifs:
            self.raiseError(node, _error.NotSupported, "if statement in list comprehension")
        self.generic_visit(node)

    def visit_List(self, node):
        self.raiseError(node, _error.NotSupported, "list")
    def visitSliceObj(self, node):
        self.raiseError(node, _error.NotSupported, "slice object")
    def visit_TryExcept(self, node):
        self.raiseError(node, _error.NotSupported, "try-except statement")
    def visit_TryFinally(self, node):
        self.raiseError(node, _error.NotSupported, "try-finally statement")

#     def visitAnd(self, node):
#         self.visitChildNodes(node)
            
#     def visitOr(self, node):
#         self.visitChildNodes(node)
        
    def visit_Assign(self, node):
        if len(node.targets) > 1:
            self.raiseError(node, _error.NotSupported, "multiple assignments")
        self.visit(node.targets[0])
        self.visit(node.value)
        
    def visit_Call(self, node):
        if node.starargs:
            self.raiseError(node, _error.NotSupported, "extra positional arguments")
        if node.kwargs:
            self.raiseError(node, _error.NotSupported, "extra named arguments")
        # f = eval(_unparse(node.node), self.tree.symdict)
        self.generic_visit(node)
                
    def visit_Compare(self, node):
        if len(node.ops) != 1:
            self.raiseError(node, _error.NotSupported, "chained comparison")
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        if node.args.vararg or node.args.kwarg:
            self.raiseError(node, _error.NotSupported, "extra positional or named arguments")
        if not self.toplevel:
            self.raiseError(node, _error.NotSupported, "embedded function definition")
        self.toplevel = False
        node.argnames = [arg.id for arg in node.args.args]
        # don't visit decorator lists - they can support more than other calls
        self.visitList(node.body)
        
    def flattenIf(self, node, tests):
        """ Flatten if-then-else as in compiler package."""
        tests.append((node.test, node.body))
        if isinstance(node.orelse, ast.If):
            self.flattenIf(node.orelse, tests)
        else:
            node.tests = tests
            node.else_ = node.orelse

    def visit_If(self, node):
        node.ignore = False
        if not node.orelse:
            test = node.test
            if isinstance(test, ast.Name):
                if test.id == '__debug__':
                    node.ignore = True
                    return # skip
        tests = []
        self.flattenIf(node, tests)
        self.generic_visit(node)

    def visit_Print(self, node):
        if node.dest is not None:
            self.raiseError(node, _error.NotSupported, "printing to a file with >> syntax")
        if not node.nl:
            self.raiseError(node, _error.NotSupported, "printing without newline")
        




def getNrBits(obj):
    if hasattr(obj, '_nrbits'):
        return obj._nrbits
    return None

def hasType(obj, theType):
    if isinstance(obj, theType):
        return True
    if isinstance(obj, Signal):
        if isinstance(obj._val, theType):
            return True
    return False


class ReferenceStack(list):
    def push(self):
        self.append(set())
    def add(self, item):
        self[-1].add(item)
    def __contains__(self, item):
        for s in self:
            if item in s:
                return True
        return False

# auxiliary types to aid type checking
## class _EdgeDetector(object):
##     pass

class _Ram(object):
    __slots__ = ['elObj', 'depth']


class _Rom(object):
    __slots__ = ['rom']
    def __init__(self, rom):
        self.rom = rom


def _maybeNegative(obj):
    if hasattr(obj, '_min') and (obj._min is not None) and (obj._min < 0):
        return True
    if isinstance(obj, (int, long)) and obj < 0:
        return True
    return False

re_str = re.compile(r"[^%]+")
re_ConvSpec = re.compile(r"%(?P<justified>[-]?)(?P<width>[0-9]*)(?P<conv>[sd])")

class ConvSpec(object):
    def __init__(self, **kwargs):
        self.justified = "RIGHT"
        self.width = 0
        self.conv = str
        if kwargs['justified'] == '-':
            self.justified = "LEFT"
        if kwargs['width']:
            self.width = int(kwargs['width'])
        if kwargs['conv'] == 'd':
            self.conv = int

defaultConvSpec = ConvSpec(**re_ConvSpec.match(r"%s").groupdict())
        

class _AnalyzeVisitor(ast.NodeVisitor, _ConversionMixin):
    
    def __init__(self, tree):
        tree.sigdict = {}
        tree.vardict = {}
        tree.inputs = set()
        tree.outputs = set()
        tree.argnames = []
        tree.kind = None
        tree.hasYield = 0
        tree.hasRom = False
        tree.hasPrint = False
        self.tree = tree
        self.labelStack = []
        self.refStack = ReferenceStack()
        self.globalRefs = set()
        self.access = _access.INPUT
        self.kind = _kind.NORMAL


#     def binaryOp(self, node, *args):
#         self.visit(node.left)
#         self.visit(node.right)
#         node.obj = int(-1)
#         node.signed = node.left.signed or node.right.signed
#     visitAdd = binaryOp
#     visitFloorDiv = binaryOp
#     visitLeftShift = binaryOp
#     visitMul = binaryOp
#     visitPower = binaryOp
#     visitMod = binaryOp
#     visitRightShift = binaryOp
#     visitSub = binaryOp


    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        node.obj = int(-1)
        node.signed = node.left.signed or node.right.signed
       
    
#     def multiBitOp(self, node, *args):
#         node.signed = False
#         for n in node.nodes:
#             self.visit(n)
#             if n.signed:
#                 node.signed = True
#         node.obj = None
#         for n in node.nodes:
#             if node.obj is None:
#                 node.obj = n.obj
#             elif isinstance(node.obj, type(n.obj)):
#                 node.obj = n.obj
#     def visitBitand(self, node, *args):
#         self.multiBitOp(node, *args)
#     def visitBitor(self, node, *args):
#         self.multiBitOp(node, *args)
#     def visitBitxor(self, node, *args):
#         self.multiBitOp(node, *args)
#     def multiLogicalOp(self, node, *args):
#         for n in node.nodes:
#             self.visit(n, *args)
#         for n in node.nodes:
#             if not hasType(n.obj, bool):
#                 self.raiseError(node, _error.NotSupported, "non-boolean argument in logical operator")
#         node.obj = bool()
#     def visitAnd(self, node, *args):
#         self.multiLogicalOp(node, *args)
#     def visitOr(self, node, *args):
#         self.multiLogicalOp(node, *args)


    def visit_BoolOp(self, node):
        for n in node.values:
            self.visit(n)
        for n in node.values:
            if not hasType(n.obj, bool):
                self.raiseError(node, _error.NotSupported, "non-boolean argument in logical operator")
        node.obj = bool()


    # unaryOp's
#     def visitInvert(self, node, *args):
#         self.visit(node.expr)
#         node.obj = node.expr.obj
#         node.signed = node.expr.signed
#     def visitNot(self, node, *args):
#         self.visit(node.expr)
#         node.obj = bool()
#         node.signed = node.expr.signed
#     def visitUnaryAdd(self, node, *args):
#         self.visit(node.expr)
#         node.obj = int(-1)
#         node.signed = node.expr.signed
#     def visitUnarySub(self, node, *args):
#         self.visit(node.expr)
#         node.obj = int(-1)
#         node.signed = node.expr.signed
#         if isinstance(node.expr, astNode.Const):
#             node.signed = True

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        op = node.op
        node.obj = node.operand.obj
        node.signed = node.operand.signed
        if isinstance(op, ast.Not):
            node.obj = bool()
        elif isinstance(op, ast.UAdd):
            node.obj = int(-1)
        elif isinstance(op, ast.USub):
            node.obj = int(-1)
            if isinstance(node.operand, ast.Num):
                node.signed = True
        
        
#     def visitAssAttr(self, node, access=_access.OUTPUT, *args):
#         if node.attrname != 'next':
#             self.raiseError(node, _error.NotSupported, "attribute assignment")
#         self.tree.kind = _kind.TASK
#         self.visit(node.expr, _access.OUTPUT)


#     def visitGetattr(self, node, *args):
#         self.visit(node.expr, *args)
#         node.obj = None
#         node.signed = False
#         if isinstance(node.expr, astNode.Name):
#             n = node.expr.name
#             if (n not in self.tree.vardict) and (n not in self.tree.symdict):
#                 raise AssertionError("attribute target: %s" % n)
#         obj = node.expr.obj
#         if isinstance(obj, Signal):
#             if node.attrname == 'posedge':
#                 node.obj = obj.posedge
#             elif node.attrname == 'negedge':
#                 node.obj = obj.negedge
#             elif node.attrname in ('val', 'next'):
#                 node.obj = obj.val
#         if isinstance(obj, (intbv, Signal)):
#             if node.attrname == 'min':
#                 node.obj = obj.min
#             elif node.attrname == 'max':
#                 node.obj = obj.max
#             elif node.attrname == 'signed':
#                 node.obj = intbv.signed
#         if isinstance(obj, EnumType):
#             assert hasattr(obj, node.attrname)
#             node.obj = getattr(obj, node.attrname)
#             if obj not in _enumTypeSet:
#                 _enumTypeSet.add(obj)
#                 suf = _genUniqueSuffix.next()
#                 obj._setName(n+suf)
#         if node.obj is None: # attribute lookup failed
#             self.raiseError(node, _error.UnsupportedAttribute, node.attrname)
            


    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setAttr(node)
        else:
            self.getAttr(node)
 
    def setAttr(self, node):
        if node.attr != 'next':
            self.raiseError(node, _error.NotSupported, "attribute assignment")
        self.tree.kind = _kind.TASK
        # self.access = _access.OUTPUT
        self.visit(node.value)
        # self.access = _access.INPUT

    def getAttr(self, node):
        self.visit(node.value)
        node.obj = None
        node.signed = False
        if isinstance(node.value, ast.Name):
            n = node.value.id
            if (n not in self.tree.vardict) and (n not in self.tree.symdict):
                raise AssertionError("attribute target: %s" % n)
        obj = node.value.obj
        if isinstance(obj, Signal):
            if node.attr == 'posedge':
                node.obj = obj.posedge
            elif node.attr == 'negedge':
                node.obj = obj.negedge
            elif node.attr in ('val', 'next'):
                node.obj = obj.val
        if isinstance(obj, (intbv, Signal)):
            if node.attr == 'min':
                node.obj = obj.min
            elif node.attr == 'max':
                node.obj = obj.max
            elif node.attr == 'signed':
                node.obj = intbv.signed
        if isinstance(obj, EnumType):
            assert hasattr(obj, node.attr)
            node.obj = getattr(obj, node.attr)
            if obj not in _enumTypeSet:
                _enumTypeSet.add(obj)
                suf = _genUniqueSuffix.next()
                obj._setName(n+suf)
        if node.obj is None: # attribute lookup failed
            self.raiseError(node, _error.UnsupportedAttribute, node.attr)
            

        
#     def visitAssign(self, node, access=_access.OUTPUT, *args):
#         target, expr = node.targets[0], node.expr
#         self.visit(target, _access.OUTPUT)
#         if isinstance(target, astNode.AssName):
#             self.visit(expr, _access.INPUT, _kind.DECLARATION)
#             node.kind = _kind.DECLARATION
#             n = target.name
#             if n in self.tree.sigdict:
#                 self.raiseError(node, _error.ShadowingVar)
#             obj = self.getObj(expr)
#             if obj is None:
#                 self.raiseError(node, _error.TypeInfer, n)
#             if isinstance(obj, intbv):
#                 if len(obj) == 0:
#                     self.raiseError(node, _error.IntbvBitWidth, n)
# ##                 if obj._min < 0:
# ##                     self.raiseError(node, _error.IntbvSign, n)
#                     if obj._min < 0:
#                         _signed = True
#             if n in self.tree.vardict:
#                 curObj = self.tree.vardict[n]
#                 if isinstance(obj, type(curObj)):
#                     pass
#                 elif isinstance(curObj, type(obj)):
#                      self.tree.vardict[n] = obj
#                 else:
#                     self.raiseError(node, _error.TypeMismatch, n)
#                 if getNrBits(obj) != getNrBits(curObj):
#                     self.raiseError(node, _error.NrBitsMismatch, n)
#             else:
#                 self.tree.vardict[n] = obj
#         else:
#             self.visit(expr, _access.INPUT)


    def visit_Assign(self, node):
        target, value = node.targets[0], node.value
        self.access = _access.OUTPUT
        self.visit(target)
        self.access = _access.INPUT
        if isinstance(target, ast.Name):
            node.kind = _kind.DECLARATION
            self.kind = _kind.DECLARATION
            self.visit(value)
            self.kind = _kind.NORMAL
            n = target.id
            if n in self.tree.sigdict:
                self.raiseError(node, _error.ShadowingVar)
            obj = self.getObj(value)
            if obj is None:
                self.raiseError(node, _error.TypeInfer, n)
            if isinstance(obj, intbv):
                if len(obj) == 0:
                    self.raiseError(node, _error.IntbvBitWidth, n)
                    if obj._min < 0:
                        _signed = True
            if n in self.tree.vardict:
                curObj = self.tree.vardict[n]
                if isinstance(obj, type(curObj)):
                    pass
                elif isinstance(curObj, type(obj)):
                     self.tree.vardict[n] = obj
                else:
                    self.raiseError(node, _error.TypeMismatch, n)
                if getNrBits(obj) != getNrBits(curObj):
                    self.raiseError(node, _error.NrBitsMismatch, n)
            else:
                self.tree.vardict[n] = obj
        else:
            self.visit(value)



        
#     def visitAugAssign(self, node, access=_access.INPUT, *args):
#         self.visit(node.node, _access.INOUT)
#         self.visit(node.expr, _access.INPUT)


    def visit_AugAssign(self, node):
        self.access = _access.INOUT
        self.visit(node.target)
        self.access = _access.INPUT
        self.visit(node.value)


#     def visitBreak(self, node, *args):
#         self.labelStack[-2].isActive = True

    def visit_Break(self, node):
        self.labelStack[-2].isActive = True
        

#     def visitCallFunc(self, node, *args):
#         self.visit(node.node)
#         for arg in node.args:
#             self.visit(arg, _access.UNKNOWN)
#         argsAreInputs = True
#         f = self.getObj(node.node)
#         node.obj = None
#         node.signed = False
#         if type(f) is type and issubclass(f, intbv):
#             node.obj = self.getVal(node)
#         elif f is concat:
#             node.obj = self.getVal(node)
#         elif f is len:
#             node.obj = int(0) # XXX
#         elif f is bool:
#             node.obj = bool()
#         elif f in (int, long, ord):
#             node.obj = int(-1)
# ##         elif f in (posedge , negedge):
# ##             node.obj = _EdgeDetector()
#         elif f is delay:
#             node.obj = delay(0)
#         ### suprize: identity comparison on unbound methods doesn't work in python 2.5??
#         elif f == intbv.signed:
#             node.obj = int(-1)
#             node.signed = True
#         elif f in myhdlObjects:
#             pass
#         elif f in builtinObjects:
#             pass
#         elif type(f) is FunctionType:
#             argsAreInputs = False
#             s = inspect.getsource(f)
#             s = s.lstrip()
#             tree = compiler.parse(s)
#             # print tree
#             fname = f.__name__
#             tree.name = _Label(fname)
#             tree.sourcefile = inspect.getsourcefile(f)
#             tree.lineoffset = inspect.getsourcelines(f)[1]-1
#             tree.symdict = f.func_globals.copy()
#             if fname in self.tree.callstack:
#                 self.raiseError(node, _error.NotSupported, "Recursive call")
#             tree.callstack = self.tree.callstack[:]
#             tree.callstack.append(fname)
#             # handle free variables
#             if f.func_code.co_freevars:
#                 for n, c in zip(f.func_code.co_freevars, f.func_closure):
#                     obj = _cell_deref(c)
#                     if not  isinstance(obj, (int, long, Signal)):
#                         self.raiseError(node, _error.FreeVarTypeError, n)
#                     tree.symdict[n] = obj
#             v = _FirstPassVisitor(tree)
#             compiler.walk(tree, v)
#             v = _AnalyzeFuncVisitor(tree, node.args)
#             compiler.walk(tree, v)
#             node.obj = tree.returnObj
#             node.tree = tree
#             for i, arg in enumerate(node.args):
#                 if isinstance(arg, astNode.Keyword):
#                     n = arg.name
#                 else: # Name
#                     n = tree.argnames[i]
#                 if n in tree.outputs:
#                     self.visit(arg, _access.OUTPUT)
#                 if n in tree.inputs:
#                     self.visit(arg, _access.INPUT)
#         elif type(f) is MethodType:
#             self.raiseError(node,_error.NotSupported, "method call: '%s'" % f.__name__)
#         else:
#             raise AssertionError("Unexpected callable")
#         if argsAreInputs:
#             for arg in node.args:
#                 self.visit(arg, _access.INPUT)



    def visit_Call(self, node):
        self.visit(node.func)
        self.access = _access.UNKNOWN
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw)
        self.access = _access.INPUT
        argsAreInputs = True
        f = self.getObj(node.func)
        node.obj = None
        node.signed = False
        if type(f) is type and issubclass(f, intbv):
            node.obj = self.getVal(node)
        elif f is concat:
            node.obj = self.getVal(node)
        elif f is len:
            node.obj = int(0) # XXX
        elif f is bool:
            node.obj = bool()
        elif f in (int, long, ord):
            node.obj = int(-1)
##         elif f in (posedge , negedge):
##             node.obj = _EdgeDetector()
        elif f is delay:
            node.obj = delay(0)
        ### suprize: identity comparison on unbound methods doesn't work in python 2.5??
        elif f == intbv.signed:
            node.obj = int(-1)
            node.signed = True
        elif f in myhdlObjects:
            pass
        elif f in builtinObjects:
            pass
        elif type(f) is FunctionType:
            argsAreInputs = False
            s = inspect.getsource(f)
            s = _dedent(s)
            tree = ast.parse(s)
            # print ast.dump(tree)
            # print tree
            fname = f.__name__
            tree.name = _Label(fname)
            tree.sourcefile = inspect.getsourcefile(f)
            tree.lineoffset = inspect.getsourcelines(f)[1]-1
            tree.symdict = f.func_globals.copy()
            if fname in self.tree.callstack:
                self.raiseError(node, _error.NotSupported, "Recursive call")
            tree.callstack = self.tree.callstack[:]
            tree.callstack.append(fname)
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    if not  isinstance(obj, (int, long, Signal)):
                        self.raiseError(node, _error.FreeVarTypeError, n)
                    tree.symdict[n] = obj
            v = _FirstPassVisitor(tree)
            v.visit(tree)
            v = _AnalyzeFuncVisitor(tree, node.args, node.keywords)
            v.visit(tree)
            node.obj = tree.returnObj
            node.tree = tree
            tree.argnames = argnames = [arg.id for arg in tree.body[0].args.args]
            # extend argument list with keyword arguments on the correct position
            node.args.extend([None]*len(node.keywords))
            for kw in node.keywords:
                node.args[argnames.index(kw.arg)] = kw.value
            for n, arg in zip(argnames, node.args):
                if n in tree.outputs:
                    self.access = _access.OUTPUT
                    self.visit(arg)
                    self.access = _access.INPUT
                if n in tree.inputs:
                    self.visit(arg)
        elif type(f) is MethodType:
            self.raiseError(node,_error.NotSupported, "method call: '%s'" % f.__name__)
        else:
            raise AssertionError("Unexpected callable")
        if argsAreInputs:
            for arg in node.args:
                self.visit(arg)


            
#     def visitCompare(self, node, *args):
#         node.obj = bool()
#         node.signed = False
#         for n in node.getChildNodes():
#             self.visit(n, *args)
#             if n.signed:
#                 node.signed = True
#         op, arg = node.ops[0]
# ##         node.expr.target = self.getObj(arg)
# ##         arg.target = self.getObj(node.expr)
#         # detect specialized case for the test
#         if op == '==' and isinstance(node.expr, astNode.Name):
#             n = node.expr.name
#             # check wether it can be a case
#             if isinstance(arg.obj, EnumItemType):
#                 node.case = (node.expr, arg.obj)
#             # check whether it can be part of an edge check
#             elif n in self.tree.sigdict:
#                 sig = self.tree.sigdict[n]
#                 v = self.getValue(arg)
#                 if v is not None:
#                     if v == 0:
#                         node.edge = sig.negedge
#                     elif v == 1:
#                         node.edge = sig.posedge


    def visit_Compare(self, node):
        node.obj = bool()
        node.signed = False
        #for n in ast.iter_child_nodes(node):
        for n in [node.left] + node.comparators:
            self.visit(n)
            if n.signed:
                node.signed = True
        op, arg = node.ops[0], node.comparators[0]
##         node.expr.target = self.getObj(arg)
##         arg.target = self.getObj(node.expr)
        # detect specialized case for the test
        if isinstance(op, ast.Eq) and isinstance(node.left, ast.Name):
            n = node.left.id
            # check wether it can be a case
            if isinstance(arg.obj, EnumItemType):
                node.case = (node.expr, arg.obj)
            # check whether it can be part of an edge check
            elif n in self.tree.sigdict:
                sig = self.tree.sigdict[n]
                v = self.getValue(arg)
                if v is not None:
                    if v == 0:
                        node.edge = sig.negedge
                    elif v == 1:
                        node.edge = sig.posedge

                        

#     def visitConst(self, node, *args):
#         node.signed = False
#         if node.value in (0, 1):
#             node.obj = bool(node.value)
#         elif isinstance(node.value, (int, str)):
#             node.obj = node.value
#         else:
#             node.obj = None


    def visit_Num(self, node):
        node.signed = False
        n = node.n
        if n in (0, 1):
            node.obj = bool(n)
        elif isinstance(n, int):
            node.obj = n
        else:
            node.obj = None

    def visit_Str(self, node):
        node.signed = False
        node.obj = node.s

            
 #    def visitContinue(self, node, *args):
#         self.labelStack[-1].isActive = True

    def visit_Continue(self, node):
        self.labelStack[-1].isActive = True

            
#     def visitFor(self, node, *args):
#         node.breakLabel = _Label("BREAK")
#         node.loopLabel = _Label("LOOP")
#         self.labelStack.append(node.breakLabel)
#         self.labelStack.append(node.loopLabel)
#         self.refStack.push()
#         self.visit(node.assign)
#         var = node.assign.name
#         self.tree.vardict[var] = int(-1)
        
#         cf = node.list
#         self.visit(cf)
#         self.require(node, isinstance(cf, astNode.CallFunc), "Expected (down)range call")
#         f = self.getObj(cf.node)
#         self.require(node, f in (range, downrange), "Expected (down)range call")
        
#         self.visit(node.body, *args)
#         self.refStack.pop()
#         self.require(node, node.else_ is None, "for-else not supported")
#         self.labelStack.pop()
#         self.labelStack.pop()


    def visit_For(self, node):
        node.breakLabel = _Label("BREAK")
        node.loopLabel = _Label("LOOP")
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.refStack.push()
        self.visit(node.target)
        var = node.target.id
        self.tree.vardict[var] = int(-1)
        
        cf = node.iter
        self.visit(cf)
        self.require(node, isinstance(cf, ast.Call), "Expected (down)range call")
        f = self.getObj(cf.func)
        self.require(node, f in (range, downrange), "Expected (down)range call")
        
        for stmt in node.body:
            self.visit(stmt)
        self.refStack.pop()
        self.require(node, not node.orelse, "for-else not supported")
        self.labelStack.pop()
        self.labelStack.pop()



#     def visitFunction(self, node, *args):
#         raise AssertionError("subclass must implement this")


    def visit_FunctionDef(self, node):
        raise AssertionError("subclass must implement this")

                  
            
#     def visitIf(self, node, *args):
#         if node.ignore:
#             return
#         for test, suite in node.tests:
#             self.visit(test, *args)
#             self.refStack.push()
#             self.visit(suite, *args)
#             self.refStack.pop()
#         if node.else_:
#             self.refStack.push()
#             self.visit(node.else_, *args)
#             self.refStack.pop()
#         # check whether the if can be mapped to a (parallel) case
#         node.isCase = node.isFullCase = False
#         test1 = node.tests[0][0]
#         if not hasattr(test1, 'case'):
#             return
#         var1, item1 = test1.case
#         # don't infer a case if there's no elsif test
#         if not node.tests[1:]:
#             return
#         choices = set()
#         choices.add(item1._index)
#         for test, suite in node.tests[1:]:
#             if not hasattr(test, 'case'):
#                 return
#             var, item = test.case
#             if var.name != var1.name or type(item) is not type(item1):
#                 return
#             if item._index in choices:
#                 return
#             choices.add(item._index)
#         node.isCase = True
#         node.caseVar = var1
#         if (len(choices) == item1._nritems) or (node.else_ is not None):
#             node.isFullCase = True


            

    def visit_If(self, node):
        if node.ignore:
            return
        for test, suite in node.tests:
            self.visit(test)
            self.refStack.push()
            self.visitList(suite)
            self.refStack.pop()
        if node.else_:
            self.refStack.push()
            self.visitList(node.else_)
            self.refStack.pop()
        # check whether the if can be mapped to a (parallel) case
        node.isCase = node.isFullCase = False
        test1 = node.tests[0][0]
        if not hasattr(test1, 'case'):
            return
        var1, item1 = test1.case
        # don't infer a case if there's no elsif test
        if not node.tests[1:]:
            return
        choices = set()
        choices.add(item1._index)
        for test, suite in node.tests[1:]:
            if not hasattr(test, 'case'):
                return
            var, item = test.case
            if var.name != var1.name or type(item) is not type(item1):
                return
            if item._index in choices:
                return
            choices.add(item._index)
        node.isCase = True
        node.caseVar = var1
        if (len(choices) == item1._nritems) or (node.else_ is not None):
            node.isFullCase = True


            
#     def visitListComp(self, node, *args):
#         mem = node.obj = _Ram()
#         self.visit(node.expr, _access.INPUT, _kind.DECLARATION)
#         mem.elObj = self.getObj(node.expr)
#         if not isinstance(mem.elObj, intbv) or not len(mem.elObj) > 0:
#             self.raiseError(node, _error.UnsupportedListComp)
#         cf = node.quals[0].list
#         self.visit(cf)
#         if not isinstance(cf, astNode.CallFunc):
#             self.raiseError(node, _error.UnsupportedListComp)
#         f = self.getObj(cf.node)
#         if f is not range or len(cf.args) != 1:
#             self.raiseError(node, _error.UnsupportedListComp)
#         mem.depth = cf.args[0].obj


    def visit_ListComp(self, node):
        mem = node.obj = _Ram()
        self.kind = _kind.DECLARATION
        self.visit(node.elt)
        self.kind = _kind.NORMAL
        mem.elObj = self.getObj(node.elt)
        if not isinstance(mem.elObj, intbv) or not len(mem.elObj) > 0:
            self.raiseError(node, _error.UnsupportedListComp)
        cf = node.generators[0].iter
        self.visit(cf)
        if not isinstance(cf, ast.Call):
            self.raiseError(node, _error.UnsupportedListComp)
        f = self.getObj(cf.func)
        if f is not range or len(cf.args) != 1:
            self.raiseError(node, _error.UnsupportedListComp)
        mem.depth = cf.args[0].obj


#     def visitAssName(self, node, *args):
#         n = node.name
#         if n in ("__verilog__", "__vhdl__"):
#             self.raiseError(node, _error.NotSupported,
#                             "%s in generator function" % n)
#         # XXX ?
#         if n in self.globalRefs:
#             self.raiseError(node, _error.UnboundLocal, n) 
#         self.refStack.add(n)




#     def visitName(self, node, access=_access.INPUT, *args):
#         n = node.name
#         node.obj = None
#         if n not in self.refStack:
#             if n in self.tree.vardict:
#                 self.raiseError(node, _error.UnboundLocal, n)
#             self.globalRefs.add(n)
#         if n in self.tree.sigdict:
#             node.obj = sig = self.tree.sigdict[n]
#             if not isinstance(sig, Signal):
#                 # print "not a signal: %s" % n
#                 pass 
#             else:
#                 if sig._type is bool:
#                     node.edge = sig.posedge
#             if access == _access.INPUT:
#                 self.tree.inputs.add(n)
#             elif access == _access.OUTPUT:
#                 self.tree.kind = _kind.TASK
#                 if n in self.tree.outputs:
#                     node.kind = _kind.REG
#                 self.tree.outputs.add(n)
#             elif access == _access.UNKNOWN:
#                 pass
#             else: 
#                 self.raiseError(node, _error.NotSupported, "Augmented signal assignment")
#         if n in self.tree.vardict:
#             obj = self.tree.vardict[n]
#             if access == _access.INOUT:
#                 # upgrade bool to int for augmented assignments
#                 if isinstance(obj, bool):
#                     obj = int(0)
#                     self.tree.vardict[n] = obj
#             node.obj = obj
#         elif n in self.tree.symdict:
#             node.obj = self.tree.symdict[n]
#             if _isTupleOfInts(node.obj):
#                 node.obj = _Rom(node.obj)
#                 self.tree.hasRom = True
#             elif isinstance(node.obj, int):
#                 node.value = node.obj
#         elif n in __builtin__.__dict__:
#             node.obj = __builtin__.__dict__[n]
#         else:
#             pass
#         node.signed = _maybeNegative(node.obj)
# ##         node.target = node.obj

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.setName(node)
        else:
            self.getName(node)

    def setName(self, node):
        # XXX INOUT access in Store context, unlike with compiler
        # XXX check whether ast context is correct
        n = node.id
        if self.access == _access.INOUT: # augmented assign
            if n in self.tree.sigdict:
                sig = self.tree.sigdict[n]
                if isinstance(sig, Signal):
                    self.raiseError(node, _error.NotSupported, "Augmented signal assignment")
            if n in self.tree.vardict:
                obj = self.tree.vardict[n]
                # upgrade bool to int for augmented assignments
                if isinstance(obj, bool):
                    obj = int(0)
                    self.tree.vardict[n] = obj
            node.obj = obj
        else:
            if n in ("__verilog__", "__vhdl__"):
                    self.raiseError(node, _error.NotSupported,
                                    "%s in generator function" % n)
            if n in self.globalRefs:
                self.raiseError(node, _error.UnboundLocal, n)
            self.refStack.add(n)

    def getName(self, node):
        n = node.id
        node.obj = None
        if n not in self.refStack:
            if n in self.tree.vardict:
                self.raiseError(node, _error.UnboundLocal, n)
            self.globalRefs.add(n)
        if n in self.tree.sigdict:
            node.obj = sig = self.tree.sigdict[n]
            if not isinstance(sig, Signal):
                # print "not a signal: %s" % n
                pass 
            else:
                if sig._type is bool:
                    node.edge = sig.posedge
            if self.access == _access.INPUT:
                self.tree.inputs.add(n)
            elif self.access == _access.OUTPUT:
                self.tree.kind = _kind.TASK
                if n in self.tree.outputs:
                    node.kind = _kind.REG
                self.tree.outputs.add(n)
            elif self.access == _access.UNKNOWN:
                pass
            else: 
                self.raiseError(node, _error.NotSupported, "Augmented signal assignment")
        if n in self.tree.vardict:
            obj = self.tree.vardict[n]
            if self.access == _access.INOUT: # probably dead code
                # upgrade bool to int for augmented assignments
                if isinstance(obj, bool):
                    obj = int(0)
                    self.tree.vardict[n] = obj
            node.obj = obj
        elif n in self.tree.symdict:
            node.obj = self.tree.symdict[n]
            if _isTupleOfInts(node.obj):
                node.obj = _Rom(node.obj)
                self.tree.hasRom = True
            elif isinstance(node.obj, int):
                node.value = node.obj
        elif n in __builtin__.__dict__:
            node.obj = __builtin__.__dict__[n]
        else:
            pass
        node.signed = _maybeNegative(node.obj)
##         node.target = node.obj





#     def visitReturn(self, node, *args):
#         self.raiseError(node, _error.NotSupported, "return statement")
        
    def visit_Return(self, node):
        self.raiseError(node, _error.NotSupported, "return statement")
        
#     def visitPrintnl(self, node, *args):
#         self.tree.hasPrint = True
#         f = []
#         nr = 0
#         a = []
#         for n in node.nodes:
#             if isinstance(n, astNode.Mod) and \
#                (isinstance(n.left, astNode.Const) and isinstance(n.left.value, str)):
#                 if isinstance(n.right, astNode.Tuple):
#                     a.extend(n.right.nodes)
#                 else:
#                     a.append(n.right)
#                 s = n.left.value
#                 while s:
#                     if not s:
#                         break
#                     if s[:2] == "%%":
#                         f.append("%")
#                         s = s[2:]
#                         continue
#                     m = re_ConvSpec.match(s)
#                     if m:
#                         c = ConvSpec(**m.groupdict())
#                         if c.justified != "RIGHT":
#                             self.raiseError(node,_error.UnsupportedFormatString,
#                                             "format justification specification: %s" %s)
#                         if c.width != 0:
#                             self.raiseError(node,_error.UnsupportedFormatString,
#                                             "format width specification: %s" %s)
#                         f.append(c)
#                         s = s[m.end():]
#                         nr += 1
#                         continue
#                     m = re_str.match(s)
#                     if m:
#                         f.append(s[:m.end()])
#                         s = s[m.end():]
#                         continue
#                     self.raiseError(node, _error.UnsupportedFormatString, "%s" % s)
#             else:
#                 f.append(defaultConvSpec)
#                 a.append(n)
#                 nr += 1
#             f.append(" ")
#         # remove last single space if it exists
#         if f:
#             f.pop()
#         node.format = f
#         node.args = a
#         if len(node.args) < nr:
#             self.raiseError(node, _error.FormatString, "not enough arguments")
#         if len(node.args) > nr:
#             self.raiseError(node, _error.FormatString, "too many arguments")
#         self.visitChildNodes(node, *args)
        
#     visitPrint = visitPrintnl



    def visit_Print(self, node):
        self.tree.hasPrint = True
        f = []
        nr = 0
        a = []
        for n in node.values:
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and \
               isinstance(n.left, ast.Str):
                if isinstance(n.right, ast.Tuple):
                    a.extend(n.right.elts)
                else:
                    a.append(n.right)
                s = n.left.s
                while s:
                    if not s:
                        break
                    if s[:2] == "%%":
                        f.append("%")
                        s = s[2:]
                        continue
                    m = re_ConvSpec.match(s)
                    if m:
                        c = ConvSpec(**m.groupdict())
                        if c.justified != "RIGHT":
                            self.raiseError(node,_error.UnsupportedFormatString,
                                            "format justification specification: %s" %s)
                        if c.width != 0:
                            self.raiseError(node,_error.UnsupportedFormatString,
                                            "format width specification: %s" %s)
                        f.append(c)
                        s = s[m.end():]
                        nr += 1
                        continue
                    m = re_str.match(s)
                    if m:
                        f.append(s[:m.end()])
                        s = s[m.end():]
                        continue
                    self.raiseError(node, _error.UnsupportedFormatString, "%s" % s)
            else:
                f.append(defaultConvSpec)
                a.append(n)
                nr += 1
            f.append(" ")
        # remove last single space if it exists
        if f:
            f.pop()
        node.format = f
        node.args = a
        if len(node.args) < nr:
            self.raiseError(node, _error.FormatString, "not enough arguments")
        if len(node.args) > nr:
            self.raiseError(node, _error.FormatString, "too many arguments")
        self.generic_visit(node)
        
  
    
#     def visitSlice(self, node, access=_access.INPUT, kind=_kind.NORMAL, *args):
#         node.signed = False
#         self.visit(node.expr, access)
#         node.obj = self.getObj(node.expr)
#         if node.lower:
#             self.visit(node.lower, _access.INPUT)
#         if node.upper:
#             self.visit(node.upper, _access.INPUT)
#         if isinstance(node.obj , intbv):
#             if kind == _kind.DECLARATION:
#                 self.require(node.lower, "Expected leftmost index")
#                 leftind = self.getVal(node.lower)
#                 if node.upper:
#                     rightind = self.getVal(node.upper)
#                 else:
#                     rightind = 0
#                 node.obj = node.obj[leftind:rightind]
    
 
#     def visitSubscript(self, node, access=_access.INPUT, *args):
#         self.visit(node.expr, access)
#         assert len(node.subs) == 1
#         self.visit(node.subs[0], _access.INPUT)
#         if isinstance(node.expr.obj, _Ram):
#             if node.flags == 'OP_ASSIGN':
#                 self.raiseError(node, _error.ListElementAssign)
#             else:
#                 node.obj = node.expr.obj.elObj
#         elif _isMem(node.expr.obj):
#             node.obj = node.expr.obj[0]
#         elif isinstance(node.expr.obj, _Rom):
#             node.obj = int(-1)
#         elif isinstance(node.expr.obj, intbv):
#             node.obj = bool()
#         else:
#             node.obj = bool() # XXX default
#         node.signed = _maybeNegative(node.obj)


    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            self.accessSlice(node)
        else:
            self.accessIndex(node)

    def accessSlice(self, node):
        node.signed = False
        self.visit(node.value)
        node.obj = self.getObj(node.value)
        self.access = _access.INPUT
        lower, upper = node.slice.lower, node.slice.upper
        if lower:
            self.visit(lower)
        if upper:
            self.visit(upper)
        if isinstance(node.obj , intbv):
            if self.kind == _kind.DECLARATION:
                self.require(lower, "Expected leftmost index")
                leftind = self.getVal(lower)
                if upper:
                    rightind = self.getVal(upper)
                else:
                    rightind = 0
                node.obj = node.obj[leftind:rightind]
    
    def accessIndex(self, node):
        self.visit(node.value)
        self.access = _access.INPUT
        self.visit(node.slice.value)
        if isinstance(node.value.obj, _Ram):
            if isinstance(node.ctx, ast.Store):
                self.raiseError(node, _error.ListElementAssign)
            else:
                node.obj = node.value.obj.elObj
        elif _isMem(node.value.obj):
            node.obj = node.value.obj[0]
        elif isinstance(node.value.obj, _Rom):
            node.obj = int(-1)
        elif isinstance(node.value.obj, intbv):
            node.obj = bool()
        else:
            node.obj = bool() # XXX default
        node.signed = _maybeNegative(node.obj)




#     def visitTuple(self, node, *args):
#         node.signed = False
#         self.visitChildNodes(node, *args)


    def visit_Tuple(self, node):
        node.signed = False
        self.generic_visit(node)



#     def visitWhile(self, node, *args):
#         node.breakLabel = _Label("BREAK")
#         node.loopLabel = _Label("LOOP")
#         self.labelStack.append(node.breakLabel)
#         self.labelStack.append(node.loopLabel)
#         self.visit(node.test, *args)
#         self.refStack.push()
#         self.visit(node.body, *args)
#         self.refStack.pop()
#         y = node.body.nodes[0]
#         if isinstance(y, astNode.Discard):
#             y = y.expr
#         if node.test.obj == True and \
#            isinstance(y, astNode.Yield) and \
#            not self.tree.hasYield > 1 and \
#            not isinstance(self.getObj(y.value), delay):
#             node.kind = _kind.ALWAYS
#             self.tree.senslist = y.senslist
#         self.require(node, node.else_ is None, "while-else not supported")
#         self.labelStack.pop()
#         self.labelStack.pop()


    def visit_While(self, node):
        node.breakLabel = _Label("BREAK")
        node.loopLabel = _Label("LOOP")
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.visit(node.test)
        self.refStack.push()
        for n in node.body:
            self.visit(n)
        self.refStack.pop()
        y = node.body[0]
        if isinstance(y, ast.Expr):
            y = y.value
        if node.test.obj == True and \
           isinstance(y, ast.Yield) and \
           not self.tree.hasYield > 1 and \
           not isinstance(self.getObj(y.value), delay):
            node.kind = _kind.ALWAYS
            self.tree.senslist = y.senslist
        self.require(node, not node.orelse, "while-else not supported")
        self.labelStack.pop()
        self.labelStack.pop()



#     def visitYield(self, node, *args):
#         self.tree.hasYield += 1
#         n = node.value
#         self.visit(n)
#         senslist = []
#         if isinstance(n, astNode.Tuple):
#             for n in n.nodes:
#                 if not isinstance(n.obj, (Signal, _WaiterList)):
#                     self.raiseError(node, _error.UnsupportedYield)
#                 senslist.append(n.obj)
#         elif isinstance(n.obj, (Signal, _WaiterList, delay)):
#             senslist = [n.obj]
#         elif _isMem(n.obj):
#             senslist = n.obj
#         else:
#             self.raiseError(node, _error.UnsupportedYield)
#         node.senslist = senslist


    def visit_Yield(self, node, *args):
        self.tree.hasYield += 1
        n = node.value
        self.visit(n)
        senslist = []
        if isinstance(n, ast.Tuple):
            for n in n.elts:
                if not isinstance(n.obj, (Signal, _WaiterList)):
                    self.raiseError(node, _error.UnsupportedYield)
                senslist.append(n.obj)
        elif isinstance(n.obj, (Signal, _WaiterList, delay)):
            senslist = [n.obj]
        elif _isMem(n.obj):
            senslist = n.obj
        else:
            self.raiseError(node, _error.UnsupportedYield)
        node.senslist = senslist



##     def visitModule(self, node, *args):
##         self.visit(node.node)
##         for n in self.tree.inputs:
##             s = self.tree.sigdict[n]
##             s._read = True
        
        

class _AnalyzeBlockVisitor(_AnalyzeVisitor):
    
    def __init__(self, tree):
        _AnalyzeVisitor.__init__(self, tree)
        for n, v in self.tree.symdict.items():
            if isinstance(v, Signal):
                self.tree.sigdict[n] = v
        
#     def visitFunction(self, node, *args):
#         self.refStack.push()
#         self.visit(node.code)
#         self.tree.kind = _kind.ALWAYS
#         for n in node.code.nodes[:-1]:
#             if not self.getKind(n) == _kind.DECLARATION:
#                 self.tree.kind = _kind.INITIAL
#                 break
#         if self.tree.kind == _kind.ALWAYS:
#             w = node.code.nodes[-1]
#             if not self.getKind(w) == _kind.ALWAYS:
#                 self.tree.kind = _kind.INITIAL
#         self.refStack.pop()


    def visit_FunctionDef(self, node):
        self.refStack.push()
        for n in node.body:
            self.visit(n)
        self.tree.kind = _kind.ALWAYS
        for n in node.body[:-1]:
            if not self.getKind(n) == _kind.DECLARATION:
                self.tree.kind = _kind.INITIAL
                break
        if self.tree.kind == _kind.ALWAYS:
            w = node.body[-1]
            if not self.getKind(w) == _kind.ALWAYS:
                self.tree.kind = _kind.INITIAL
        self.refStack.pop()




                
#     def visitModule(self, node, *args):
#         self.visit(node.node)
#         for n in self.tree.outputs:
#             s = self.tree.sigdict[n]
#             if s._driven:
#                 self.raiseError(node, _error.SigMultipleDriven, n)
#             s._driven = "reg"
#         for n in self.tree.inputs:
#             s = self.tree.sigdict[n]
#             s._read = True

    def visit_Module(self, node):
        self.generic_visit(node)
        for n in self.tree.outputs:
            s = self.tree.sigdict[n]
            if s._driven:
                self.raiseError(node, _error.SigMultipleDriven, n)
            s._driven = "reg"
        for n in self.tree.inputs:
            s = self.tree.sigdict[n]
            s._read = True
            
#     def visitReturn(self, node, *args):
#         ### value should be None
#         if isinstance(node.value, astNode.Const) and node.value.value is None:
#             obj = None
#         elif isinstance(node.value, astNode.Name) and node.value.name == 'None':
#             obj = None
#         else:
#             self.raiseError(node, _error.NotSupported, "return value other than None")
     
    def visit_Return(self, node):
        ### value should be None
        if node.value is None:
            pass
        elif isinstance(node.value, ast.Name) and node.value.id == "None":
            pass
        else:
            self.raiseError(node, _error.NotSupported, "return value other than None")




class _AnalyzeAlwaysCombVisitor(_AnalyzeBlockVisitor):
    
    def __init__(self, tree, senslist):
        _AnalyzeBlockVisitor.__init__(self, tree)
        self.tree.senslist = senslist

#     def visitFunction(self, node, *args):
#           self.refStack.push()
#           self.visit(node.code)
#           self.tree.kind = _kind.SIMPLE_ALWAYS_COMB
#           for n in node.code.nodes:
#               if isinstance(n, astNode.Assign) and \
#                  isinstance(n.nodes[0], astNode.AssAttr) and \
#                  self.getKind(n.nodes[0].expr) != _kind.REG:
#                   pass
#               else:
#                   self.tree.kind = _kind.ALWAYS_COMB
#                   return
#           # rom access is expanded into a case statement
#           if self.tree.hasRom:
#               self.tree.kind = _kind.ALWAYS_COMB
#           self.refStack.pop()

    def visit_FunctionDef(self, node):
          self.refStack.push()
          for n in node.body:
              self.visit(n)
          self.tree.kind = _kind.SIMPLE_ALWAYS_COMB
          for n in node.body:
              if isinstance(n, ast.Assign) and \
                 isinstance(n.targets[0], ast.Attribute) and \
                 self.getKind(n.targets[0].value) != _kind.REG:
                  pass
              else:
                  self.tree.kind = _kind.ALWAYS_COMB
                  return
          # rom access is expanded into a case statement
          if self.tree.hasRom:
              self.tree.kind = _kind.ALWAYS_COMB
          self.refStack.pop()



    def visit_Module(self, node):
        _AnalyzeBlockVisitor.visit_Module(self, node)
        if self.tree.kind == _kind.SIMPLE_ALWAYS_COMB:
            for n in self.tree.outputs:
                s = self.tree.sigdict[n]
                s._driven = "wire"



                

class _AnalyzeAlwaysDecoVisitor(_AnalyzeBlockVisitor):
    
    def __init__(self, tree, senslist):
        _AnalyzeBlockVisitor.__init__(self, tree)
        self.tree.senslist = senslist

#     def visitFunction(self, node, *args):
#           self.refStack.push()
#           self.visit(node.code)
#           self.tree.kind = _kind.ALWAYS_DECO
#           self.refStack.pop()
         
    def visit_FunctionDef(self, node):
          self.refStack.push()
          for n in node.body:
              self.visit(n)
          self.tree.kind = _kind.ALWAYS_DECO
          self.refStack.pop()
         
            
            

class _AnalyzeFuncVisitor(_AnalyzeVisitor):
    
    def __init__(self, tree, args, keywords):
        _AnalyzeVisitor.__init__(self, tree)
        self.args = args
        self.keywords = keywords
        self.tree.hasReturn = False
        self.tree.returnObj = None

#     def visitFunction(self, node, *args):
#         self.refStack.push()
#         argnames = node.argnames
#         for i, arg in enumerate(self.args):
#             if isinstance(arg, astNode.Keyword):
#                 n = arg.name
#                 self.tree.symdict[n] = self.getObj(arg.expr)
#             else: # Name
#                 n = argnames[i]
#                 self.tree.symdict[n] = self.getObj(arg)
#             self.tree.argnames.append(n)
#         for n, v in self.tree.symdict.items():
#             if isinstance(v, (Signal, intbv)):
#                 self.tree.sigdict[n] = v
#         self.visit(node.code)
#         self.refStack.pop()
#         if self.tree.hasYield:
#             self.raiseError(node, _error.NotSupported,
#                             "call to a generator function")
#         if self.tree.kind == _kind.TASK:
#             if self.tree.returnObj is not None:
#                 self.raiseError(node, _error.NotSupported,
#                                 "function with side effects and return value")
#         else:
#             if self.tree.returnObj is None:
#                 self.raiseError(node, _error.NotSupported,
#                                 "pure function without return value")
        
    def visit_FunctionDef(self, node):
        self.refStack.push()
        argnames = [arg.id for arg in node.args.args]
        for i, arg in enumerate(self.args):
            n = argnames[i]
            self.tree.symdict[n] = self.getObj(arg)
            self.tree.argnames.append(n)
        for kw in self.keywords:
            n = kw.arg
            self.tree.symdict[n] = self.getObj(kw.value)
            self.tree.argnames.append(n)
        for n, v in self.tree.symdict.items():
            if isinstance(v, (Signal, intbv)):
                self.tree.sigdict[n] = v
        for stmt in node.body:
            self.visit(stmt)
        self.refStack.pop()
        if self.tree.hasYield:
            self.raiseError(node, _error.NotSupported,
                            "call to a generator function")
        if self.tree.kind == _kind.TASK:
            if self.tree.returnObj is not None:
                self.raiseError(node, _error.NotSupported,
                                "function with side effects and return value")
        else:
            if self.tree.returnObj is None:
                self.raiseError(node, _error.NotSupported,
                                "pure function without return value")


   
#     def visitReturn(self, node, *args):
#         self.visit(node.value, _access.INPUT, _kind.DECLARATION, *args)
#         if isinstance(node.value, astNode.Const) and node.value.value is None:
#             obj = None
#         elif isinstance(node.value, astNode.Name) and node.value.name == 'None':
#             obj = None
#         elif node.value.obj is not None:
#             obj = node.value.obj
#         else:
#             self.raiseError(node, _error.ReturnTypeInfer)
#         if isinstance(obj, intbv) and len(obj) == 0:
#             self.raiseError(node, _error.ReturnIntbvBitWidth)
#         if self.tree.hasReturn:
#             returnObj = self.tree.returnObj
#             if isinstance(obj, type(returnObj)):
#                 pass
#             elif isinstance(returnObj, type(obj)):
#                 self.tree.returnObj = obj
#             else:
#                 self.raiseError(node, _error.ReturnTypeMismatch)
#             if getNrBits(obj) != getNrBits(returnObj):
#                 self.raiseError(node, _error.ReturnNrBitsMismatch)
#         else:
#             self.tree.returnObj = obj
#             self.tree.hasReturn = True


    def visit_Return(self, node):
        self.kind = _kind.DECLARATION
        if node.value is not None:
            self.visit(node.value)
        self.kind = _kind.NORMAL
        if node.value is None:
            obj = None
        elif isinstance(node.value, ast.Name) and node.value.id == 'None':
            obj = None
        elif node.value.obj is not None:
            obj = node.value.obj
        else:
            self.raiseError(node, _error.ReturnTypeInfer)
        if isinstance(obj, intbv) and len(obj) == 0:
            self.raiseError(node, _error.ReturnIntbvBitWidth)
        if self.tree.hasReturn:
            returnObj = self.tree.returnObj
            if isinstance(obj, type(returnObj)):
                pass
            elif isinstance(returnObj, type(obj)):
                self.tree.returnObj = obj
            else:
                self.raiseError(node, _error.ReturnTypeMismatch)
            if getNrBits(obj) != getNrBits(returnObj):
                self.raiseError(node, _error.ReturnNrBitsMismatch)
        else:
            self.tree.returnObj = obj
            self.tree.hasReturn = True



       
def _analyzeTopFunc(func, *args, **kwargs):
    tree = _makeAST(func)
    v = _AnalyzeTopFuncVisitor(*args, **kwargs)
    v.visit(tree)
    return v
      
    
class _AnalyzeTopFuncVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.name = None
        self.argdict = {}
    
#     def visitFunction(self, node):
#         self.name = node.name
#         argnames = node.argnames
#         i=-1
#         for i, arg in enumerate(self.args):
#             if isinstance(arg, Signal):
#                 n = argnames[i]
#                 self.argdict[n] = arg
#         for n in argnames[i+1:]:
#             if n in self.kwargs:
#                 arg = self.kwargs[n]
#                 if isinstance(arg, Signal):
#                     self.argdict[n] = arg
#         self.argnames = [n for n in argnames if n in self.argdict]


    def visit_FunctionDef(self, node):
        self.name = node.name
        argnames = [arg.id for arg in node.args.args]
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


