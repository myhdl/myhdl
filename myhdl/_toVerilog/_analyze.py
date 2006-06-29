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

""" myhdl toVerilog analysis module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import inspect
import compiler
from compiler import ast as astNode
from sets import Set
from types import GeneratorType, FunctionType, ClassType, MethodType
from cStringIO import StringIO
import re
import __builtin__

import myhdl
from myhdl import *
from myhdl import ToVerilogError
from myhdl._unparse import _unparse
from myhdl._cell_deref import _cell_deref
from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
from myhdl._delay import delay
from myhdl._toVerilog import _error, _access, _kind, _context, \
                             _ToVerilogMixin, _Label
from myhdl._extractHierarchy import _isMem, _UserDefinedVerilog

myhdlObjects = myhdl.__dict__.values()
builtinObjects = __builtin__.__dict__.values()


def _makeName(n, prefixes):
    if len(prefixes) > 1:
        name = '_' + '_'.join(prefixes[1:]) + '_' + n
    else:
        name = n
    if '[' in name or ']' in name:
        name = "\\" + name + ' '
##     print prefixes
##     print name
    return name
                    
def _analyzeSigs(hierarchy):
    curlevel = 0
    siglist = []
    memlist = []
    prefixes = []
    
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
                raise ToVerilogError(_error.UndefinedBitWidth, s._name)
            siglist.append(s)
        # list of signals
        for n, m in memdict.items():
            if m.name is not None:
                continue
            m.name = _makeName(n, prefixes)
            memlist.append(m)

    # handle the case where a named signal appears in a list also; such a list
    # is not declared and references to it in a generator will be flagged as an error 
    for m in memlist:
        for s in m.mem:
            if s._name is not None:
                m.decl = False
                break
        if not m.decl:
            continue
        for i, s in enumerate(m.mem):
            s._name = "%s[%s]" % (m.name, i)
            if not s._nrbits:
                raise ToVerilogError(_error.UndefinedBitWidth, s._name)
            if type(s.val) != type(m.elObj.val):
                raise ToVerilogError(_error.InconsistentType, s._name)
            if s._nrbits != m.elObj._nrbits:
                raise ToVerilogError(_error.InconsistentBitWidth, s._name)
            
    return siglist, memlist

        

def _analyzeGens(top, absnames):
    genlist = []
    for g in top:
        if isinstance(g, _UserDefinedVerilog):
            ast = g
        elif isinstance(g, (_AlwaysComb, _Always)):
            f = g.func
            s = inspect.getsource(f)
            # remove decorators
            s = re.sub(r"@.*", "", s)
            s = s.lstrip()
            ast = compiler.parse(s)
            #print ast
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.func_globals.copy()
            ast.callstack = []
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    if isinstance(g, _AlwaysComb):
                        assert isinstance(obj, (int, long, Signal)) or \
                               _isMem(obj) or isTupleOfInts(obj)
                    ast.symdict[n] = obj
            ast.name = absnames.get(id(g), str(_Label("BLOCK"))).upper()
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            if isinstance(g, _AlwaysComb):
                v = _AnalyzeAlwaysCombVisitor(ast, g.senslist)
            else:
                v = _AnalyzeAlwaysDecoVisitor(ast, g.senslist)
            compiler.walk(ast, v)
        else:
            f = g.gi_frame
            s = inspect.getsource(f)
            # remove decorators
            s = re.sub(r"@.*", "", s)
            s = s.lstrip()
            ast = compiler.parse(s)
            #print ast
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.f_globals.copy()
            ast.symdict.update(f.f_locals)
            ast.callstack = []
            ast.name = absnames.get(id(g), str(_Label("BLOCK"))).upper()
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            v = _AnalyzeBlockVisitor(ast)
            compiler.walk(ast, v)
        genlist.append(ast)
    return genlist


class _NotSupportedVisitor(_ToVerilogMixin):
    
    def __init__(self, ast):
        self.ast = ast
        self.toplevel = True
        
    def visitAssList(self, node, *args):
        self.raiseError(node, _error.NotSupported, "list assignment")
    def visitAssTuple(self, node, *args):
        self.raiseError(node, _error.NotSupported, "tuple assignment")
    def visitBackquote(self, node, *args):
        self.raiseError(node, _error.NotSupported, "backquote")
    def visitClass(self, node, *args):
        self.raiseError(node, _error.NotSupported, "class statement")
    def visitDict(self, node, *args):
        self.raiseError(node, _error.NotSupported, "dictionary")
    def visitDiv(self, node, *args):
        self.raiseError(node, _error.NotSupported, "true division - consider '//'")
    def visitEllipsis(self, node, *args):
        self.raiseError(node, _error.NotSupported, "ellipsis")
    def visitExec(self, node, *args):
        self.raiseError(node, _error.NotSupported, "exec statement")
    def visitExpression(self, node, *args):
        self.raiseError(node, _error.NotSupported, "Expression node")
    def visitFrom(self, node, *args):
        self.raiseError(node, _error.NotSupported, "from statement")
    def visitGlobal(self, node, *args):
        self.raiseError(node, _error.NotSupported, "global statement")
    def visitImport(self, node, *args):
        self.raiseError(node, _error.NotSupported, "import statement")
    def visitLambda(self, node, *args):
        self.raiseError(node, _error.NotSupported, "lambda statement")
    def visitListComp(self, node, *args):
        if len(node.quals) > 1:
            self.raiseError(node, _error.NotSupported, "multiple for statements in list comprehension")
        self.visitChildNodes(node)
    def visitListCompIf(self, node, *args):
        self.raiseError(node, _error.NotSupported, "if statement in list comprehension")
    def visitList(self, node, *args):
        self.raiseError(node, _error.NotSupported, "list")
    def visitSliceObj(self, node):
        self.raiseError(node, _error.NotSupported, "slice object")
    def visitTryExcept(self, node, *args):
        self.raiseError(node, _error.NotSupported, "try-except statement")
    def visitTryFinally(self, node, *args):
        self.raiseError(node, _error.NotSupported, "try-finally statement")

    def visitAnd(self, node):
        self.visitChildNodes(node)
            
    def visitOr(self, node):
        self.visitChildNodes(node)
        
    def visitAssign(self, node, *args):
        if len(node.nodes) > 1:
            self.raiseError(node, _error.NotSupported, "multiple assignments")
        self.visit(node.nodes[0], *args)
        self.visit(node.expr, *args)
        
    def visitCallFunc(self, node):
        if node.star_args:
            self.raiseError(node, _error.NotSupported, "extra positional arguments")
        if node.dstar_args:
            self.raiseError(node, _error.NotSupported, "extra named arguments")
        f = eval(_unparse(node.node), self.ast.symdict)
        self.visitChildNodes(node)
                
    def visitCompare(self, node, *args):
        if len(node.ops) != 1:
            self.raiseError(node, _error.NotSupported, "chained comparison")
        self.visitChildNodes(node, *args)
        
    def visitFunction(self, node, *args):
        if node.flags != 0: # check flags
            self.raiseError(node, _error.NotSupported, "extra positional or named arguments")
        if not self.toplevel:
            self.raiseError(node, _error.NotSupported, "embedded function definition")
        self.toplevel = False
        self.visitChildNodes(node, *args)
        
    def visitIf(self, node, *args):
        node.ignore = False
        if len(node.tests) == 1 and not node.else_:
            test = node.tests[0][0]
            if isinstance(test, compiler.ast.Name):
                if test.name == '__debug__':
                    node.ignore = True
                    return # skip
        for test, suite in node.tests:
            self.visit(test)
            self.visit(suite)
        if node.else_:
            self.visit(node.else_)
        
    def visitPrintnl(self, node, *args):
        if node.dest is not None:
            self.raiseError(node, _error.NotSupported, "printing to a file with >> syntax")
        self.visitChildNodes(node, *args)
        
    visitPrint = visitPrintnl


def isTupleOfInts(obj):
    if not isinstance(obj, tuple):
        return False
    for e in obj:
        if not isinstance(e, (int, long)):
            return False
    return True

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
        self.append(Set())
    def add(self, item):
        self[-1].add(item)
    def __contains__(self, item):
        for s in self:
            if item in s:
                return True
        return False

# auxiliary types to aid type checking
class _EdgeDetector(object):
    pass

class _Ram(object):
    __slots__ = ['elObj', 'depth']


class _Rom(object):
    __slots__ = ['rom']
    def __init__(self, rom):
        self.rom = rom

def _isNegative(obj):
    if hasattr(obj, '_min') and (obj._min is not None) and (obj._min < 0):
        return True
    if isinstance(obj, (int, long)) and obj < 0:
        return True
    return False


class _AnalyzeVisitor(_ToVerilogMixin):
    
    def __init__(self, ast):
        ast.sigdict = {}
        ast.vardict = {}
        ast.inputs = Set()
        ast.outputs = Set()
        ast.argnames = []
        ast.kind = None
        ast.isGen = False
        ast.hasRom = False
        self.ast = ast
        self.labelStack = []
        self.refStack = ReferenceStack()
        self.globalRefs = Set()


    def binaryOp(self, node, *args):
        self.visit(node.left)
        self.visit(node.right)
        node.obj = int()
        node.signed = node.left.signed or node.right.signed
    visitAdd = binaryOp
    visitFloorDiv = binaryOp
    visitLeftShift = binaryOp
    visitMul = binaryOp
    visitPower = binaryOp
    visitMod = binaryOp
    visitRightShift = binaryOp
    visitSub = binaryOp
    
    def multiBitOp(self, node, *args):
        node.signed = False
        for n in node.nodes:
            self.visit(n)
            if n.signed:
                node.signed = True
        node.obj = None
        for n in node.nodes:
            if node.obj is None:
                node.obj = n.obj
            elif isinstance(node.obj, type(n.obj)):
                node.obj = n.obj
    def visitBitand(self, node, *args):
        self.multiBitOp(node, *args)
    def visitBitor(self, node, *args):
        self.multiBitOp(node, *args)
    def visitBitxor(self, node, *args):
        self.multiBitOp(node, *args)
    def multiLogicalOp(self, node, *args):
        for n in node.nodes:
            self.visit(n, *args)
        for n in node.nodes:
            if not hasType(n.obj, bool):
                self.raiseError(node, _error.NotSupported, "non-boolean argument in logical operator")
        node.obj = bool()
    def visitAnd(self, node, *args):
        self.multiLogicalOp(node, *args)
    def visitOr(self, node, *args):
        self.multiLogicalOp(node, *args)

    # unaryOp's
    def visitInvert(self, node, *args):
        self.visit(node.expr)
        node.obj = node.expr.obj
        node.signed = node.expr.signed
    def visitNot(self, node, *args):
        self.visit(node.expr)
        node.obj = bool()
        node.signed = node.expr.signed
    def visitUnaryAdd(self, node, *args):
        self.visit(node.expr)
        node.obj = int()
        node.signed = node.expr.signed
    def visitUnarySub(self, node, *args):
        self.visit(node.expr)
        node.obj = int()
        node.signed = node.expr.signed
        if isinstance(node.expr, astNode.Const):
            node.signed = True
        
    def visitAssAttr(self, node, access=_access.OUTPUT, *args):
        if node.attrname != 'next':
            self.raiseError(node, _error.NotSupported, "attribute assignment")
        self.ast.kind = _kind.TASK
        self.visit(node.expr, _access.OUTPUT)
        
    def visitAssign(self, node, access=_access.OUTPUT, *args):
        target, expr = node.nodes[0], node.expr
        self.visit(target, _access.OUTPUT)
        if isinstance(target, astNode.AssName):
            self.visit(expr, _access.INPUT, _kind.DECLARATION)
            node.kind = _kind.DECLARATION
            n = target.name
            obj = self.getObj(expr)
            if obj is None:
                self.raiseError(node, _error.TypeInfer, n)
            if isinstance(obj, intbv):
                if len(obj) == 0:
                    self.raiseError(node, _error.IntbvBitWidth, n)
##                 if obj._min < 0:
##                     self.raiseError(node, _error.IntbvSign, n)
                    if obj._min < 0:
                        _signed = True
            if n in self.ast.vardict:
                curObj = self.ast.vardict[n]
                if isinstance(obj, type(curObj)):
                    pass
                elif isinstance(curObj, type(obj)):
                     self.ast.vardict[n] = obj
                else:
                    self.raiseError(node, _error.TypeMismatch, n)
                if getNrBits(obj) != getNrBits(curObj):
                    self.raiseError(node, _error.NrBitsMismatch, n)
            else:
                self.ast.vardict[n] = obj
        else:
            self.visit(expr, _access.INPUT)

    def visitAssName(self, node, *args):
        n = node.name
        if n ==  "__verilog__":
            self.raiseError(node, _error.NotSupported,
                            "__verilog__ in generator function")
        # XXX ?
        if n in self.globalRefs:
            self.raiseError(node, _error.UnboundLocal, n)
        self.refStack.add(n)
        
    def visitAugAssign(self, node, access=_access.INPUT, *args):
        self.visit(node.node, _access.INOUT)
        self.visit(node.expr, _access.INPUT)

    def visitBreak(self, node, *args):
        self.labelStack[-2].isActive = True

    def visitCallFunc(self, node, *args):
        self.visit(node.node)
        for arg in node.args:
            self.visit(arg, _access.UNKNOWN)
        argsAreInputs = True
        f = self.getObj(node.node)
        node.obj = None
        node.signed = False
        if type(f) is type and issubclass(f, intbv):
            node.obj = self.getVal(node)
        elif f is len:
            node.obj = int() # XXX
        elif f is bool:
            node.obj = bool()
        elif f is int:
            node.obj = int()
##         elif f in (posedge , negedge):
##             node.obj = _EdgeDetector()
        elif f is delay:
            node.obj = delay(0)
        elif f in myhdlObjects:
            pass
        elif f in builtinObjects:
            pass
        elif type(f) is FunctionType:
            argsAreInputs = False
            s = inspect.getsource(f)
            s = s.lstrip()
            ast = compiler.parse(s)
            # print ast
            fname = f.__name__
            ast.name = _Label(fname)
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.func_globals.copy()
            if fname in self.ast.callstack:
                self.raiseError(node, _error.NotSupported, "Recursive call")
            ast.callstack = self.ast.callstack[:]
            ast.callstack.append(fname)
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    if not  isinstance(obj, (int, long, Signal)):
                        self.raiseError(node, _error.FreeVarTypeError, n)
                    ast.symdict[n] = obj
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            v = _AnalyzeFuncVisitor(ast, node.args)
            compiler.walk(ast, v)
            node.ast = ast
            for i, arg in enumerate(node.args):
                if isinstance(arg, astNode.Keyword):
                    n = arg.name
                else: # Name
                    n = ast.argnames[i]
                if n in ast.outputs:
                    self.visit(arg, _access.OUTPUT)
                if n in ast.inputs:
                    self.visit(arg, _access.INPUT)
        elif type(f) is MethodType:
            self.raiseError(node,_error.NotSupported, "method call: '%s'" % f.__name__)
        else:
            raise AssertionError("Unexpected callable")
        if argsAreInputs:
            for arg in node.args:
                self.visit(arg, _access.INPUT)
            
    def visitCompare(self, node, *args):
        node.obj = bool()
        node.signed = False
        for n in node.getChildNodes():
            self.visit(n, *args)
            if n.signed:
                node.signed = True
        op, arg = node.ops[0]
        # detect specialized case for the test
        if op == '==' and isinstance(node.expr, astNode.Name):
            n = node.expr.name
            # check wether it can be a case
            if isinstance(arg.obj, EnumItemType):
                node.case = (node.expr, arg.obj)
            # check whether it can be part of an edge check
            elif n in self.ast.sigdict:
                sig = self.ast.sigdict[n]
                if isinstance(arg.obj, astNode.Const):
                    v = arg.obj.value
                    if value == 0:
                        node.edge = sig.negedge
                    elif value == 1:
                        node.edge = sig.posedge
                elif isinstance(arg.obj, astNode.Name):
                    c = arg.obj.name
                    if c in self.ast.symdict:
                        a = self.ast.symdict[n]
                        if isinstance(a, int):
                            if a == 0:
                                node.edge = sig.negedge
                            elif a == 1:
                                node.edge = sig.posedge
                        

    def visitConst(self, node, *args):
        node.signed = False
        if node.value in (0, 1):
            node.obj = bool(node.value)
        elif isinstance(node.value, int):
            node.obj = node.value
        else:
            node.obj = None
            
    def visitContinue(self, node, *args):
        self.labelStack[-1].isActive = True
            
    def visitFor(self, node, *args):
        node.breakLabel = _Label("BREAK")
        node.loopLabel = _Label("LOOP")
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.refStack.push()
        self.visit(node.assign)
        var = node.assign.name
        self.ast.vardict[var] = int()
        self.visit(node.list)
        self.visit(node.body, *args)
        self.refStack.pop()
        self.require(node, node.else_ is None, "for-else not supported")
        self.labelStack.pop()
        self.labelStack.pop()

    def visitFunction(self, node, *args):
        raise AssertionError("subclass must implement this")
           
    def visitGetattr(self, node, *args):
        self.visit(node.expr, *args)
        assert isinstance(node.expr, astNode.Name)
        assert node.expr.name in self.ast.symdict
        node.obj = None
        node.signed = False
        obj = self.ast.symdict[node.expr.name]
        if isinstance(obj, Signal):
            if node.attrname in ('posedge', 'negedge'):
                node.obj = _EdgeDetector()
            elif node.attrname == 'val':
                node.obj = obj.val
        elif isinstance(obj, EnumType):
            assert hasattr(obj, node.attrname)
            node.obj = getattr(obj, node.attrname)
            
    def visitIf(self, node, *args):
        if node.ignore:
            return
        for test, suite in node.tests:
            self.visit(test, *args)
            self.refStack.push()
            self.visit(suite, *args)
            self.refStack.pop()
        if node.else_:
            self.refStack.push()
            self.visit(node.else_, *args)
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
        choices = Set()
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
            
    def visitListComp(self, node, *args):
        mem = node.obj = _Ram()
        self.visit(node.expr, _access.INPUT, _kind.DECLARATION)
        mem.elObj = self.getObj(node.expr)
        if not isinstance(mem.elObj, intbv) or not len(mem.elObj) > 0:
            self.raiseError(node, _error.UnsupportedListComp)
        cf = node.quals[0].list
        self.visit(cf)
        if not isinstance(cf, astNode.CallFunc):
            self.raiseError(node, _error.UnsupportedListComp)
        f = self.getObj(cf.node)
        if f is not range or len(cf.args) != 1:
            self.raiseError(node, _error.UnsupportedListComp)
        mem.depth = cf.args[0].obj

    def visitName(self, node, access=_access.INPUT, *args):
        n = node.name
        node.obj = None
        if n not in self.refStack:
            if n in self.ast.vardict:
                self.raiseError(node, _error.UnboundLocal, n)
            self.globalRefs.add(n)
        if n in self.ast.sigdict:
            node.obj = self.ast.sigdict[n]
            if access == _access.INPUT:
                self.ast.inputs.add(n)
            elif access == _access.OUTPUT:
                self.ast.kind = _kind.TASK
                if n in self.ast.outputs:
                    node.kind = _kind.REG
                self.ast.outputs.add(n)
            elif access == _access.UNKNOWN:
                pass
            else: 
                raise AssertionError
        if n in self.ast.vardict:
            obj = self.ast.vardict[n]
            if access == _access.INOUT:
                # upgrade bool to int for augmented assignments
                if isinstance(obj, bool):
                    obj = int()
                    self.ast.vardict[n] = obj
            node.obj = obj
        elif n in self.ast.symdict:
            node.obj = self.ast.symdict[n]
            if isTupleOfInts(node.obj):
                node.obj = _Rom(node.obj)
                self.ast.hasRom = True
        elif n in __builtin__.__dict__:
            node.obj = __builtin__.__dict__[n]
        else:
            pass
        node.signed = _isNegative(node.obj)

    def visitReturn(self, node, *args):
        self.raiseError(node, _error.NotSupported, "return statement")
            
    def visitSlice(self, node, access=_access.INPUT, kind=_kind.NORMAL, *args):
        node.signed = False
        self.visit(node.expr, access)
        node.obj = self.getObj(node.expr)
        if node.lower:
            self.visit(node.lower, _access.INPUT)
        if node.upper:
            self.visit(node.upper, _access.INPUT)
        if isinstance(node.obj , intbv):
            if kind == _kind.DECLARATION:
                self.require(node.lower, "Expected leftmost index")
                leftind = self.getVal(node.lower)
                if node.upper:
                    rightind = self.getVal(node.upper)
                else:
                    rightind = 0
                node.obj = node.obj[leftind:rightind]
            
 
    def visitSubscript(self, node, access=_access.INPUT, *args):
        node.signed = False
        self.visit(node.expr, access)
        assert len(node.subs) == 1
        self.visit(node.subs[0], _access.INPUT)
        if isinstance(node.expr.obj, _Ram):
            if node.flags == 'OP_ASSIGN':
                self.raiseError(node, _error.ListElementAssign)
            else:
                node.obj = node.expr.obj.elObj
        elif isinstance(node.expr.obj, intbv):
            node.obj = bool()
        else:
            node.obj = bool() # XXX default

    def visitWhile(self, node, *args):
        node.breakLabel = _Label("BREAK")
        node.loopLabel = _Label("LOOP")
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.visit(node.test, *args)
        self.refStack.push()
        self.visit(node.body, *args)
        self.refStack.pop()
        y = node.body.nodes[0]
        if node.test.obj == True and \
           isinstance(y, astNode.Yield) and \
           not isinstance(self.getObj(y.value), delay):
            node.kind = _kind.ALWAYS
        self.require(node, node.else_ is None, "while-else not supported")
        self.labelStack.pop()
        self.labelStack.pop()

    def visitYield(self, node, *args):
        self.ast.isGen = True
        n = node.value
        self.visit(n)
        if isinstance(n, astNode.Tuple):
            for n in n.nodes:
                if not type(n.obj) in (Signal, _EdgeDetector):
                    self.raiseError(node, _error.UnsupportedYield)
        else:
            if not type(n.obj) in (Signal, _EdgeDetector, delay):
                self.raiseError(node, _error.UnsupportedYield)
        

class _AnalyzeBlockVisitor(_AnalyzeVisitor):
    
    def __init__(self, ast):
        _AnalyzeVisitor.__init__(self, ast)
        for n, v in self.ast.symdict.items():
            if isinstance(v, Signal):
                self.ast.sigdict[n] = v
        
    def visitFunction(self, node, *args):
        self.refStack.push()
        self.visit(node.code)
        self.ast.kind = _kind.ALWAYS
        for n in node.code.nodes[:-1]:
            if not self.getKind(n) == _kind.DECLARATION:
                self.ast.kind = _kind.INITIAL
                break
        if self.ast.kind == _kind.ALWAYS:
            w = node.code.nodes[-1]
            if not self.getKind(w) == _kind.ALWAYS:
                self.ast.kind = _kind.INITIAL
        self.refStack.pop()
                
    def visitModule(self, node, *args):
        self.visit(node.node)
        for n in self.ast.outputs:
            s = self.ast.sigdict[n]
            if s._driven:
                self.raiseError(node, _error.SigMultipleDriven, n)
            s._driven = "reg"
        for n in self.ast.inputs:
            s = self.ast.sigdict[n]
            s._read = True
            
    def visitReturn(self, node, *args):
        ### value should be None
        if isinstance(node.value, astNode.Const) and node.value.value is None:
            obj = None
        elif isinstance(node.value, astNode.Name) and node.value.name == 'None':
            obj = None
        else:
            self.raiseError(node, _error.NotSupported, "return value other than None")
     

class _AnalyzeAlwaysCombVisitor(_AnalyzeBlockVisitor):
    
    def __init__(self, ast, senslist):
        _AnalyzeBlockVisitor.__init__(self, ast)
        self.ast.senslist = senslist

    def visitFunction(self, node, *args):
          self.refStack.push()
          self.visit(node.code)
          self.ast.kind = _kind.SIMPLE_ALWAYS_COMB
          for n in node.code.nodes:
              if isinstance(n, astNode.Assign) and \
                 isinstance(n.nodes[0], astNode.AssAttr) and \
                 self.getKind(n.nodes[0].expr) != _kind.REG:
                  pass
              else:
                  self.ast.kind = _kind.ALWAYS_COMB
                  return
          # rom access is expanded into a case statement
          if self.ast.hasRom:
              self.ast.kind = _kind.ALWAYS_COMB
          self.refStack.pop()

    def visitModule(self, node, *args):
        _AnalyzeBlockVisitor.visitModule(self, node, *args)
        if self.ast.kind == _kind.SIMPLE_ALWAYS_COMB:
            for n in self.ast.outputs:
                s = self.ast.sigdict[n]
                s._driven = "wire"
                

class _AnalyzeAlwaysDecoVisitor(_AnalyzeBlockVisitor):
    
    def __init__(self, ast, senslist):
        _AnalyzeBlockVisitor.__init__(self, ast)
        self.ast.senslist = senslist

    def visitFunction(self, node, *args):
          self.refStack.push()
          self.visit(node.code)
          self.ast.kind = _kind.ALWAYS_DECO
          self.refStack.pop()
         
            

class _AnalyzeFuncVisitor(_AnalyzeVisitor):
    
    def __init__(self, ast, args):
        _AnalyzeVisitor.__init__(self, ast)
        self.args = args
        self.ast.hasReturn = False
        self.ast.returnObj = None

    def visitFunction(self, node, *args):
        self.refStack.push()
        argnames = node.argnames
        for i, arg in enumerate(self.args):
            if isinstance(arg, astNode.Keyword):
                n = arg.name
                self.ast.symdict[n] = self.getObj(arg.expr)
            else: # Name
                n = argnames[i]
                self.ast.symdict[n] = self.getObj(arg)
            self.ast.argnames.append(n)
        for n, v in self.ast.symdict.items():
            if isinstance(v, (Signal, intbv)):
                self.ast.sigdict[n] = v
        self.visit(node.code)
        self.refStack.pop()
        if self.ast.isGen:
            self.raiseError(node, _error.NotSupported,
                            "call to a generator function")
        if self.ast.kind == _kind.TASK:
            if self.ast.returnObj is not None:
                self.raiseError(node, _error.NotSupported,
                                "function with side effects and return value")
        else:
            if self.ast.returnObj is None:
                self.raiseError(node, _error.NotSupported,
                                "pure function without return value")
        
        
    def visitReturn(self, node, *args):
        self.visit(node.value, _access.INPUT, _kind.DECLARATION, *args)
        if isinstance(node.value, astNode.Const) and node.value.value is None:
            obj = None
        elif isinstance(node.value, astNode.Name) and node.value.name == 'None':
            obj = None
        elif node.value.obj is not None:
            obj = node.value.obj
        else:
            self.raiseError(node, _error.ReturnTypeInfer)
        if isinstance(obj, intbv) and len(obj) == 0:
            self.raiseError(node, _error.ReturnIntbvBitWidth)
        if self.ast.hasReturn:
            returnObj = self.ast.returnObj
            if isinstance(obj, type(returnObj)):
                pass
            elif isinstance(returnObj, type(obj)):
                self.ast.returnObj = obj
            else:
                self.raiseError(node, _error.ReturnTypeMismatch)
            if getNrBits(obj) != getNrBits(returnObj):
                self.raiseError(node, _error.ReturnNrBitsMismatch)
        else:
            self.ast.returnObj = obj
            self.ast.hasReturn = True

       
def _analyzeTopFunc(func, *args, **kwargs):
    s = inspect.getsource(func)
    s = s.lstrip()
    ast = compiler.parse(s)
    v = _AnalyzeTopFuncVisitor(*args, **kwargs)
    compiler.walk(ast, v)
    return v
      
    
class _AnalyzeTopFuncVisitor(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.name = None
        self.argdict = {}
    
    def visitFunction(self, node):
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


