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
import __builtin__

import myhdl
from myhdl import *
from myhdl import ToVerilogError
from myhdl._unparse import _unparse
from myhdl._cell_deref import _cell_deref
from myhdl._always_comb import _AlwaysComb
from myhdl._toVerilog import _error, _access, _kind,_context, \
                             _ToVerilogMixin, _Label


myhdlObjects = myhdl.__dict__.values()
builtinObjects = __builtin__.__dict__.values()
 
   
def _analyzeSigs(hierarchy):
    curlevel = 0
    siglist = []
    prefixes = []
    for level, name, sigdict in hierarchy:
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta == -1:
            prefixes.append(name)
        elif delta == 0:
            prefixes.pop()
            prefixes.append(name)
        else:
            prefixes = prefixes[:curlevel]
        for n, s in sigdict.items():
            if s._name is None:
                if len(prefixes) > 1:
                    name = '_' + '_'.join(prefixes[1:]) + '_' + n
                else:
                    name = n
                if '[' in name or ']' in name:
                    name = "\\" + name + ' '
##                 name = name.replace('[', '_')
##                 name = name.replace(']', '_')
                s._name = name
                siglist.append(s)
            if not s._nrbits:
                raise ToVerilogError(_error.UndefinedBitWidth, s._name)
    return siglist

        

def _analyzeGens(top, genNames):
    genlist = []
    for g in top:
        if type(g) is _AlwaysComb:
            f = g.func
            s = inspect.getsource(f)
            s = s.lstrip()
            ast = compiler.parse(s)
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.func_globals.copy()
            ast.callstack = []
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    assert isinstance(obj, (int, long, Signal))
                    ast.symdict[n] = obj
            ast.name = genNames.get(id(g.gen), _Label("BLOCK"))
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            v = _AnalyzeAlwaysCombVisitor(ast, g.senslist)
            compiler.walk(ast, v)
        else:
            f = g.gi_frame
            s = inspect.getsource(f)
            s = s.lstrip()
            ast = compiler.parse(s)
            # print ast
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.f_globals.copy()
            ast.symdict.update(f.f_locals)
            ast.callstack = []
            ast.name = genNames.get(id(g), _Label("BLOCK"))
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
        self.raiseError(node, _error.NotSupported, "list comprehension")
    def visitList(self, node, *args):
        self.raiseError(node, _error.NotSupported, "list")
    def visitSliceObj(self, node):
        self.raiseError(node, _error.NotSupported, "slice object")
    def visitTryExcept(self, node, *args):
        self.raiseError(node, _error.NotSupported, "try-except statement")
    def visitTryFinally(self, node, *args):
        self.raiseError(node, _error.NotSupported, "try-finally statement")

    def visitAnd(self, node, context=_context.UNKNOWN):
        if not context == _context.BOOLEAN:
            self.raiseError(node, _error.NotSupported, "shortcutting logical and in non-boolean context")
        self.visitChildNodes(node, _context.BOOLEAN)
            
    def visitOr(self, node, context=_context.UNKNOWN):
        if not context == _context.BOOLEAN:
            self.raiseError(node, _error.NotSupported, "shortcutting logical or in non-boolean context")
        self.visitChildNodes(node, _context.BOOLEAN)
        
    def visitAssign(self, node, *args):
        if len(node.nodes) > 1:
            self.raiseError(node, _error.NotSupported, "multiple assignments")
        self.visit(node.nodes[0], *args)
        self.visit(node.expr, *args)
        
    def visitCallFunc(self, node, context=_context.UNKNOWN):
        if node.star_args:
            self.raiseError(node, _error.NotSupported, "extra positional arguments")
        if node.dstar_args:
            self.raiseError(node, _error.NotSupported, "extra named arguments")
        f = eval(_unparse(node.node), self.ast.symdict)
        if f is bool:
            context = _context.BOOLEAN
        self.visitChildNodes(node, context)
                
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
        for test, suite in node.tests:
            self.visit(test, _context.BOOLEAN)
            self.visit(suite, _context.UNKNOWN)
        if node.else_:
            self.visit(node.else_, _context.UNKNOWN)


def getNrBits(obj):
    if hasattr(obj, '_nrbits'):
        return obj._nrbits
    return None


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

class _AnalyzeVisitor(_ToVerilogMixin):
    
    def __init__(self, ast):
        ast.sigdict = {}
        ast.vardict = {}
        ast.inputs = Set()
        ast.outputs = Set()
        ast.argnames = []
        ast.kind = None
        ast.isGen = False
        self.ast = ast
        self.labelStack = []
        self.refStack = ReferenceStack()
        self.globalRefs = Set()


    def binaryOp(self, node, *args):
        self.visit(node.left)
        self.visit(node.right)
        node.obj = int()
    visitAdd = binaryOp
    visitFloorDiv = binaryOp
    visitLeftShift = binaryOp
    visitMul = binaryOp
    visitPow = binaryOp
    visitMod = binaryOp
    visitRightShift = binaryOp
    visitSub = binaryOp
    
    def multiBitOp(self, node, *args):
        for n in node.nodes:
            self.visit(n)
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
        node.obj = None
    def visitAnd(self, node, *args):
        self.multiLogicalOp(node, *args)
    def visitOr(self, node, *args):
        self.multiLogicalOp(node, *args)

    # unaryOp's
    def visitInvert(self, node, *args):
        self.visit(node.expr)
        node.obj = node.expr.obj
    def visitNot(self, node, *args):
        self.visit(node.expr)
        node.obj = bool()
    def visitUnaryAdd(self, node, *args):
        self.visit(node.expr)
        node.obj = int()
    def visitUnarySub(self, node, *args):
        self.visit(node.expr)
        node.obj = int()
        
    def visitAssAttr(self, node, access=_access.OUTPUT, *args):
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
                if obj._min < 0:
                    self.raiseError(node, _error.IntbvSign, n)
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
        if type(f) is type and issubclass(f, intbv):
            node.obj = self.getVal(node)
        elif f is len:
            node.obj = int() # XXX
        elif f is bool:
            node.obj = bool()
        elif f in (posedge , negedge):
            node.obj = _EdgeDetector()
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
        self.visitChildNodes(node)
        op, arg = node.ops[0]
        if op == '==':
            if isinstance(node.expr, astNode.Name) and \
               str(type(arg.obj)) == "<class 'myhdl._enum.EnumItem'>":
                node.case = (node.expr.name, arg.obj)

    def visitConst(self, node, *args):
        if isinstance(node.value, int):
            node.obj = int()
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
        obj = self.ast.symdict[node.expr.name]
        if str(type(obj)) == "<class 'myhdl._enum.Enum'>":
            assert hasattr(obj, node.attrname)
            node.obj = getattr(obj, node.attrname)
            
    def visitIf(self, node, *args):
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
        name1, item1 = test1.case
        choices = Set()
        choices.add(item1._index)
        for test, suite in node.tests[1:]:
            if not hasattr(test, 'case'):
                return
            name, item = test.case
            if name != name1 or type(item) is not type(item1):
                return
            if item._index in choices:
                return
            choices.add(item._index)
        node.isCase = True
        node.caseVar = name1
        if (len(choices) == item1._nritems) or (node.else_ is not None):
            node.isFullCase = True

    def visitName(self, node, access=_access.INPUT, *args):
        n = node.name
        if n not in self.refStack:
            if n in self.ast.vardict:
                self.raiseError(node, _error.UnboundLocal, n)
            self.globalRefs.add(n)
        if n in self.ast.sigdict:
            if access == _access.INPUT:
                self.ast.inputs.add(n)
            elif access == _access.OUTPUT:
                self.ast.kind = _kind.TASK
                self.ast.outputs.add(n)
            elif access == _access.UNKNOWN:
                pass
            else: 
                raise AssertionError
        node.obj = None
        if n in self.ast.vardict:
            node.obj = self.ast.vardict[n]
        elif n in self.ast.symdict:
            node.obj = self.ast.symdict[n]
        elif n in __builtin__.__dict__:
            node.obj = __builtins__[n]
        else:
            pass

    def visitReturn(self, node, *args):
        self.raiseError(node, _error.NotSupported, "return statement")
            
    def visitSlice(self, node, access=_access.INPUT, kind=_kind.NORMAL, *args):
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
        self.visit(node.expr, access)
        for n in node.subs:
            self.visit(n, _access.INPUT)
        node.obj = bool() # XXX 

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
        if isinstance(node.test, astNode.Const) and \
           node.test.value == True and \
           isinstance(y, astNode.Yield):
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
            if not type(n.obj) in (Signal, _EdgeDetector):
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
                self.raiseError(node, _error._SigMultipleDriven, n)
            s._driven = True
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
        _AnalyzeVisitor.__init__(self, ast)
        self.ast.senslist = senslist
        for n, v in self.ast.symdict.items():
            if isinstance(v, Signal):
                self.ast.sigdict[n] = v

    def visitFunction(self, node, *args):
          self.refStack.push()
          self.visit(node.code)
          self.ast.kind = _kind.ALWAYS_COMB
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


