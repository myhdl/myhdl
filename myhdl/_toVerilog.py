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

""" myhdl toVerilog module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import inspect
import operator
import compiler
from compiler import ast as astNode
from sets import Set
from types import GeneratorType, FunctionType, ClassType
from cStringIO import StringIO
import __builtin__

import myhdl
from myhdl import *
from myhdl import ToVerilogError
from myhdl._extractHierarchy import _HierExtr, _findInstanceName
from myhdl._util import _flatten
from myhdl._unparse import _unparse
from myhdl._cell_deref import _cell_deref
from myhdl._always_comb import _AlwaysComb
            
_converting = 0
_profileFunc = None

INPUT, OUTPUT, INOUT, \
UNKNOWN, \
NORMAL, DECLARATION, \
ALWAYS, INITIAL, ALWAYS_COMB, \
BOOLEAN = range(10)

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
_error.IntbvBitWidth = "intbv instance should have bit width"
_error.TypeInfer = "Can't infer type"
_error.ReturnTypeMismatch = "Return type mismatch"
_error.ReturnNrBitsMismatch = "Returned nr of bits mismatch"
_error.ReturnIntbvBitWidth = "Returned intbv instance should have bit width"
_error.ReturnTypeInfer = "Can't infer return type"

    
def _checkArgs(arglist):
    for arg in arglist:
        if not type(arg) in (GeneratorType, _AlwaysComb):
            raise ToVerilogError(_error.ArgType, arg)
        
def toVerilog(func, *args, **kwargs):
    global _converting
    if _converting:
        return func(*args, **kwargs) # skip
    if not callable(func):
        raise ToVerilogError(_error.FirstArgType, "got %s" % type(func))
    _converting = 1
    try:
        outer = inspect.getouterframes(inspect.currentframe())[1]
        name = _findInstanceName(outer)
        if name is None:
            raise TopLevelNameError
        h = _HierExtr(name, func, *args, **kwargs)
    finally:
        _converting = 0
    vpath = name + ".v"
    vfile = open(vpath, 'w')
    tbpath = "tb_" + vpath
    tbfile = open(tbpath, 'w')
    
    siglist = _analyzeSigs(h.hierarchy)
    arglist = _flatten(h.top)
    _checkArgs(arglist)
    genlist = _analyzeGens(arglist, h.genNames)
    intf = _analyzeTopFunc(func, *args, **kwargs)
    intf.name = name
    
    _writeModuleHeader(vfile, intf)
    _writeSigDecls(vfile, intf, siglist)
    _convertGens(genlist, vfile)
    _writeModuleFooter(vfile)
    _writeTestBench(tbfile, intf)

    vfile.close()
    tbfile.close()
    
    return h.top


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
                    s._name = '_'.join(prefixes[1:]) + '_' + n
                else:
                    s._name = n
                siglist.append(s)
            if not s._nrbits:
                raise ToVerilogError(_error.UndefinedBitWidth, s._name)
    return siglist


def LabelGenerator():
    i = 1
    while 1:
        yield "_MYHDL%s" % i
        i += 1
        
genLabel = LabelGenerator()

class Label(object):
    def __init__(self, name):
        self.name = genLabel.next() + '_' + name
        self.isActive = False
    def __str__(self):
        return str(self.name)
         

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
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    assert isinstance(obj, (int, long, Signal))
                    ast.symdict[n] = obj
            ast.name = genNames.get(id(g.gen), genLabel.next() + "_BLOCK")
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            v = _AnalyzeAlwaysCombVisitor(ast, g.senslist)
            compiler.walk(ast, v)
        else:
            f = g.gi_frame
            s = inspect.getsource(f)
            s = s.lstrip()
            ast = compiler.parse(s)
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.f_globals.copy()
            ast.symdict.update(f.f_locals)
            ast.name = genNames.get(id(g), genLabel.next() + "_BLOCK")
            v = _NotSupportedVisitor(ast)
            compiler.walk(ast, v)
            v = _AnalyzeBlockVisitor(ast)
            compiler.walk(ast, v)
        genlist.append(ast)
    return genlist


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

    def visitAnd(self, node, context=UNKNOWN):
        if not context == BOOLEAN:
            self.raiseError(node, _error.NotSupported, "shortcutting logical and in non-boolean context")
        self.visitChildNodes(node, BOOLEAN)
            
    def visitOr(self, node, context=UNKNOWN):
        if not context == BOOLEAN:
            self.raiseError(node, _error.NotSupported, "shortcutting logical or in non-boolean context")
        self.visitChildNodes(node, BOOLEAN)
        
    def visitAssign(self, node, *args):
        if len(node.nodes) > 1:
            self.raiseError(node, _error.NotSupported, "multiple assignments")
        self.visit(node.nodes[0], *args)
        self.visit(node.expr, *args)
        
    def visitCallFunc(self, node, context=UNKNOWN):
        f = eval(_unparse(node.node), self.ast.symdict)
        if f is bool:
            context = BOOLEAN
        self.visitChildNodes(node, context)
                
    def visitCompare(self, node, *args):
        if len(node.ops) != 1:
            self.raiseError(node, _error.NotSupported, "chained comparison")
        self.visitChildNodes(node, *args)
        
    def visitFunction(self, node, *args):
        if not self.toplevel:
            self.raiseError(node, _error.NotSupported, "embedded function definition")
        self.toplevel = False
        self.visitChildNodes(node, *args)
        
    def visitIf(self, node, *args):
        for test, suite in node.tests:
            self.visit(test, BOOLEAN)
            self.visit(suite, UNKNOWN)
        if node.else_:
            self.visit(node.else_, UNKNOWN)


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
    

class _AnalyzeVisitor(_ToVerilogMixin):
    
    def __init__(self, ast):
        ast.sigdict = {}
        ast.vardict = {}
        ast.inputs = Set()
        ast.outputs = Set()
        ast.argnames = []
        ast.kind = None
        ast.isTask = False
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
        
    def visitAssAttr(self, node, access=OUTPUT, *args):
        self.ast.isTask = True
        self.visit(node.expr, OUTPUT)
        
    def visitAssign(self, node, access=OUTPUT, *args):
        target, expr = node.nodes[0], node.expr
        self.visit(target, OUTPUT)
        if isinstance(target, astNode.AssName):
            self.visit(expr, INPUT, DECLARATION)
            node.kind = DECLARATION
            n = target.name
            obj = self.getObj(expr)
            if obj is None:
                self.raiseError(node, _error.TypeInfer, n)
            if isinstance(obj, intbv) and len(obj) == 0:
                self.raiseError(node, _error.IntbvBitWidth, n)
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
            self.visit(expr, INPUT)

    def visitAssName(self, node, *args):
        n = node.name
        # XXX ?
        if n in self.globalRefs:
            self.raiseError(node, _error.UnboundLocal, n)
        self.refStack.add(n)
        
    def visitAugAssign(self, node, access=INPUT, *args):
        self.visit(node.node, INOUT)
        self.visit(node.expr, INPUT)

    def visitBreak(self, node, *args):
        self.labelStack[-2].isActive = True

    def visitCallFunc(self, node, *args):
        self.visit(node.node)
        for arg in node.args:
            self.visit(arg, UNKNOWN)
        argsAreInputs = True
        f = self.getObj(node.node)
        if type(f) is type and issubclass(f, intbv):
            node.obj = intbv()
        elif f is len:
            node.obj = int() # XXX
        elif f is bool:
            node.obj = bool()
        elif f in myhdl.__dict__.values():
            pass
        elif f in __builtin__.__dict__.values():
            pass
        elif type(f) is FunctionType:
            argsAreInputs = False
            s = inspect.getsource(f)
            s = s.lstrip()
            ast = compiler.parse(s)
            # print ast
            ast.name = genLabel.next() + "_" + f.__name__
            ast.sourcefile = inspect.getsourcefile(f)
            ast.lineoffset = inspect.getsourcelines(f)[1]-1
            ast.symdict = f.func_globals.copy()
            # handle free variables
            if f.func_code.co_freevars:
                for n, c in zip(f.func_code.co_freevars, f.func_closure):
                    obj = _cell_deref(c)
                    assert isinstance(obj, (int, long, Signal))
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
                    self.visit(arg, OUTPUT)
                if n in ast.inputs:
                    self.visit(arg, INPUT)
        if argsAreInputs:
            for arg in node.args:
                self.visit(arg, INPUT)
            
    def visitCompare(self, node, *args):
        node.obj = bool()

    def visitConst(self, node, *args):
        if isinstance(node.value, int):
            node.obj = int()
        else:
            node.obj = None
            
    def visitContinue(self, node, *args):
        self.labelStack[-1].isActive = True
            
    def visitFor(self, node, *args):
        node.breakLabel = Label("BREAK")
        node.loopLabel = Label("LOOP")
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

    def visitName(self, node, access=INPUT, *args):
        n = node.name
        if n not in self.refStack:
            if n in self.ast.vardict:
                self.raiseError(node, _error.UnboundLocal, n)
            self.globalRefs.add(n)
        if n in self.ast.sigdict:
            if access == INPUT:
                self.ast.inputs.add(n)
            elif access == OUTPUT:
                self.ast.isTask = True
                self.ast.outputs.add(n)
            elif access == UNKNOWN:
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
            
    def visitSlice(self, node, access=INPUT, kind=NORMAL, *args):
        self.visit(node.expr, access)
        node.obj = self.getObj(node.expr)
        if node.lower:
            self.visit(node.lower, INPUT)
        if node.upper:
            self.visit(node.upper, INPUT)
        if isinstance(node.obj , intbv):
            if kind == DECLARATION:
                self.require(node.lower, "Expected leftmost index")
                leftind = self.getVal(node.lower)
                if node.upper:
                    rightind = self.getVal(node.upper)
                else:
                    rightind = 0
                node.obj = intbv()[leftind:rightind]
            
 
    def visitSubscript(self, node, access=INPUT, *args):
        self.visit(node.expr, access)
        for n in node.subs:
            self.visit(n, INPUT)
        node.obj = bool() # XXX 

    def visitWhile(self, node, *args):
        node.breakLabel = Label("BREAK")
        node.loopLabel = Label("LOOP")
        self.labelStack.append(node.breakLabel)
        self.labelStack.append(node.loopLabel)
        self.visit(node.test, *args)
        self.refStack.push()
        self.visit(node.body, *args)
        self.refStack.pop()
        if isinstance(node.test, astNode.Const) and \
           node.test.value == True and \
           isinstance(node.body.nodes[0], astNode.Yield):
            node.kind = ALWAYS
        self.require(node, node.else_ is None, "while-else not supported")
        self.labelStack.pop()
        self.labelStack.pop()
        

class _AnalyzeBlockVisitor(_AnalyzeVisitor):
    
    def __init__(self, ast):
        _AnalyzeVisitor.__init__(self, ast)
        for n, v in self.ast.symdict.items():
            if isinstance(v, Signal):
                self.ast.sigdict[n] = v
        
    def visitFunction(self, node, *args):
        self.refStack.push()
        self.visit(node.code)
        self.ast.kind = ALWAYS
        for n in node.code.nodes[:-1]:
            if not self.getKind(n) == DECLARATION:
                self.ast.kind = INITIAL
                break
        if self.ast.kind == ALWAYS:
            w = node.code.nodes[-1]
            if not self.getKind(w) == ALWAYS:
                self.ast.kind = INITIAL
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
        self.raiseError(node, _error.NotSupported, "return statement")
        

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
          self.ast.kind = ALWAYS_COMB
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
        
    def visitReturn(self, node, *args):
        self.visit(node.value, INPUT, DECLARATION, *args)
        if isinstance(node.value, astNode.Const) and node.value.value is None:
            obj = None
        elif isinstance(node.value, astNode.Name) and node.value.name is None:
            obj = None
        elif node.value.obj is not None:
            obj = node.value.obj
        else:
            self.raiseError(node, error._ReturnTypeInfer)
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
        if node.flags != 0: # check flags
            raise AssertionError("unsupported function type")
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


### Verilog output functions ###

def _writeModuleHeader(f, intf):
    print >> f, "module %s (" % intf.name
    b = StringIO()
    for portname in intf.argnames:
        print >> b, "    %s," % portname
    print >> f, b.getvalue()[:-2]
    b.close()
    print >> f, ");"
    print >> f
    for portname in intf.argnames:
        s = intf.argdict[portname]
        assert (s._name == portname)
        r = _getRangeString(s)
        if s._driven:
            print >> f, "output %s%s;" % (r, portname)
            print >> f, "reg %s%s;" % (r, portname)
        else:
            print >> f, "input %s%s;" % (r, portname)
    print >> f


def _writeSigDecls(f, intf, siglist):
    for s in siglist:
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        if s._driven:
            print >> f, "reg %s%s;" % (r, s._name)
        elif s._read:
            raise ToVerilogError(_error.UndrivenSignal, s._name)
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
        return "[%s:0] " % (s._nrbits-1)
    else:
        raise AssertionError


def _convertGens(genlist, vfile):
    blockBuf = StringIO()
    funcBuf = StringIO()
    for ast in genlist:
        if ast.kind == ALWAYS:
            Visitor = _ConvertAlwaysVisitor
        elif ast.kind == INITIAL:
            Visitor = _ConvertInitialVisitor
        else: # ALWAYS_COMB
            Visitor = _ConvertAlwaysCombVisitor
        v = Visitor(ast, blockBuf, funcBuf)
        compiler.walk(ast, v)
    vfile.write(funcBuf.getvalue()); funcBuf.close()
    vfile.write(blockBuf.getvalue()); blockBuf.close()

YIELD, PRINT = range(2)

class _ConvertVisitor(_ToVerilogMixin):
    
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

    def writeDeclaration(self, obj, name, dir):
        if dir: dir = dir + ' '
        if type(obj) is bool:
            self.write("%s%s;" % (dir, name))
        elif isinstance(obj, int):
            if dir == "input ":
                self.write("input %s;" % name)
                self.writeline()
            self.write("integer %s;" % name)
        elif hasattr(obj, '_nrbits'):
            self.write("%s[%s-1:0] %s;" % (dir, obj._nrbits, name))
        else:
            raise AssertionError("var %s has unexpected type %s" % (name, type(obj)))

    def writeDeclarations(self):
        for name, obj in self.ast.vardict.items():
            self.writeline()
            self.writeDeclaration(obj, name, "reg")
                
    def indent(self):
        self.ind += ' ' * 4

    def dedent(self):
        self.ind = self.ind[:-4]

    def binaryOp(self, node, op=None):
        self.write("(")
        self.visit(node.left)
        self.write(" %s " % op)
        self.visit(node.right)
        self.write(")")
    def visitAdd(self, node, *args):
        self.binaryOp(node, '+')
    def visitFloorDiv(self, node, *args):
        self.binaryOp(node, '/')
    def visitLeftShift(self, node, *args):
        self.binaryOp(node, '<<')
    def visitMod(self, node, context=None, *args):
        if context == PRINT:
            self.visit(node.left)
            self.write(", ")
            self.visit(node.right)
        else:
            self.binaryOp(node, '%')        
    def visitMul(self, node, *args):
        self.binaryOp(node, '*')
    def visitPower(self, node, *args):
         self.binaryOp(node, '**')
    def visitSub(self, node, *args):
        self.binaryOp(node, "-")
    def visitRightShift(self, node, *args):
        self.binaryOp(node, '>>')
        
    def multiOp(self, node, op):
        self.write("(")
        self.visit(node.nodes[0])
        for node in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(node)
        self.write(")")
    def visitAnd(self, node, *args):
        self.multiOp(node, '&&')
    def visitBitand(self, node, *args):
        self.multiOp(node, '&')
    def visitBitor(self, node, *args):
        self.multiOp(node, '|')
    def visitBitxor(self, node, *args):
        self.multiOp(node, '^')
    def visitOr(self, node, *args):
        self.multiOp(node, '||')

    def unaryOp(self, node, op):
        self.write("(%s" % op)
        self.visit(node.expr)
        self.write(")")
    def visitInvert(self, node, *args):
        self.unaryOp(node, '~')
    def visitNot(self, node, *args):
        self.unaryOp(node, '!')
    def visitUnaryAdd(self, node, *args):
        self.unaryOp(node, '+')
    def visitUnarySub(self, node, *args):
        self.unaryOp(node, '-')

    def visitAssAttr(self, node, *args):
        if node.attrname != 'next':
            self.raiseError(node, _error.NotSupported, "attribute assignment")
        self.isSigAss = True
        self.visit(node.expr)

    def visitAssert(self, node, *args):
        # XXX
        pass

    def visitAssign(self, node, *args):
        assert len(node.nodes) == 1
        self.visit(node.nodes[0])
        if self.isSigAss:
            self.write(' <= ')
            self.isSigAss = False
        else:
            self.write(' = ')
        self.visit(node.expr)
        self.write(';')

    def visitAssName(self, node, *args):
        self.write(node.name)

    def visitAugAssign(self, node, *args):
        opmap = {"+=" : "+",
                 "-=" : "-",
                 "*=" : "*",
                 "//=" : "/",
                 "%=" : "%",
                 "**=" : "**",
                 "|=" : "|",
                 ">>=" : ">>",
                 "<<=" : "<<",
                 "&=" : "&",
                 "^=" : "^"
                 }
        if node.op not in opmap:
            self.raiseError(node, _error.NotSupported,
                            "augmented assignment %s" % node.op)
        op = opmap[node.op]
        self.visit(node.node)
        self.write(" = ")
        self.visit(node.node)
        self.write(" %s " % op)
        self.visit(node.expr)
        self.write(";")
         
    def visitBreak(self, node, *args):
        self.write("disable %s;" % self.labelStack[-2])

    def visitCallFunc(self, node, *args):
        fn = node.node
        assert isinstance(fn, astNode.Name)
        f = self.getObj(fn)
        opening, closing = '(', ')'
        if f is bool:
            self.write("(")
            self.visit(node.args[0])
            self.write(" ? 1'b1 : 1'b0)")
            return
        elif f is len:
            val = self.getVal(node)
            self.require(node, val is not None, "cannot calculate len")
            self.write(`val`)
            return
        elif type(f)  in (ClassType, type) and issubclass(f, Exception):
            self.write(f.__name__)
        elif f is concat:
            opening, closing = '{', '}'
        elif hasattr(node, 'ast'):
            self.write(node.ast.name)
        else:
            self.write(f.__name__)
        if node.args:
            self.write(opening)
            self.visit(node.args[0])
            for arg in node.args[1:]:
                self.write(", ")
                self.visit(arg)
            self.write(closing)
        if hasattr(node, 'ast'):
            if node.ast.isTask:
                Visitor = _ConvertTaskVisitor
            else:
                Visitor = _ConvertFunctionVisitor
            v = Visitor(node.ast, self.funcBuf)
            compiler.walk(node.ast, v)

    def visitCompare(self, node, *args):
        self.write("(")
        self.visit(node.expr)
        op, code = node.ops[0]
        self.write(" %s " % op)
        self.visit(code)
        self.write(")")

    def visitConst(self, node, context=None, *args):
        if context == PRINT:
            assert type(node.value) is str
            self.write('"Verilog %s"' % node.value)
        else:
            self.write(node.value)

    def visitContinue(self, node, *args):
        self.write("disable %s;" % self.labelStack[-1])

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
            self.visit(step)
        self.write(") begin")
        if node.loopLabel.isActive:
            self.write(": %s" % node.loopLabel)
        self.indent()
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()

    def visitFunction(self, node, *args):
        raise AssertionError("To be implemented in subclass")

    def visitGetattr(self, node, *args):
        assert isinstance(node.expr, astNode.Name)
        assert node.expr.name in self.ast.symdict
        obj = self.ast.symdict[node.expr.name]
        if type(obj) is Signal:
            if node.attrname == 'next':
                self.isSigAss = True
            self.visit(node.expr)
        elif str(type(obj)) == "<class 'myhdl._enum.Enum'>":
            assert hasattr(obj, node.attrname)
            e = getattr(obj, node.attrname)
            self.write("%d'b%s" % (obj._nrbits, e._val))
        
    def visitIf(self, node, *args):
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
            self.visit(suite)
            self.dedent()
            self.writeline()
            self.write("end")
        if node.else_:
            self.writeline()
            self.write("else begin")
            self.indent()
            self.visit(node.else_)
            self.dedent()
            self.writeline()
            self.write("end")

    def visitKeyword(self, node, *args):
        self.visit(node.expr)
       
    def visitName(self, node, *args):
        n = node.name
        if n == 'False':
            self.write("1'b0")
        elif n == 'True':
            self.write("1'b1")
        elif n in self.ast.vardict:
            self.write(n)
        elif n in self.ast.argnames:
            self.write(n)
        elif node.name in self.ast.symdict:
            obj = self.ast.symdict[n]
            if isinstance(obj, int):
                self.write(str(obj))
            elif type(obj) is Signal:
                self.write(obj._name)
            else:
                self.write(n)
        else:
            raise AssertionError("name ref: %s" % n)

    def visitPass(self, node, *args):
        self.write("// pass")

    def handlePrint(self, node):
        assert len(node.nodes) == 1
        s = node.nodes[0]
        self.write('$display(')
        self.visit(s, PRINT)
        self.write(');')
    
    def visitPrint(self, node, *args):
        self.handlePrint(node)

    def visitPrintnl(self, node, *args):
        self.handlePrint(node)
    
    def visitRaise(self, node, *args):
        self.write('$display("Verilog: ')
        self.visit(node.expr1)
        self.write('");')
        self.writeline()
        self.write("$finish;")
        
    def visitReturn(self, node, *args):
        self.write("disable %s;" % self.returnLabel)

    def visitSlice(self, node, *args):
        if isinstance(node.expr, astNode.CallFunc) and \
           node.expr.node.obj is intbv:
            c = self.getVal(node)
            self.write("%s'h" % c._nrbits)
            self.write("%x" % c._val)
            return
        self.visit(node.expr)
        self.write("[")
        if node.lower is None:
            self.write("%s" % node.obj._nrbits)
        else:
            self.visit(node.lower)
        self.write("-1:")
        if node.upper is None:
            self.write("0")
        else:
            self.visit(node.upper)
        self.write("]")

    def visitStmt(self, node, *args):
        for stmt in node.nodes:
            self.writeline()
            self.visit(stmt)
            # ugly hack to detect an orphan "task" call
            if isinstance(stmt, astNode.CallFunc) and hasattr(stmt, 'ast'):
                self.write(';')

    def visitSubscript(self, node, *args):
        self.visit(node.expr)
        self.write("[")
        assert len(node.subs) == 1
        self.visit(node.subs[0])
        self.write("]")

    def visitTuple(self, node, context=None, *args):
        assert context != None
        if context == PRINT:
            sep = ", "
        else:
            sep = " or "
        tpl = node.nodes
        self.visit(tpl[0])
        for elt in tpl[1:]:
            self.write(sep)
            self.visit(elt)

    def visitWhile(self, node, *args):
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
        self.visit(node.body)
        self.dedent()
        self.writeline()
        self.write("end")
        if node.breakLabel.isActive:
            self.writeline()
            self.write("end")
        self.labelStack.pop()
        self.labelStack.pop()
        
    def visitYield(self, node, *args):
        self.write("@ (")
        self.visit(node.value, YIELD)
        self.write(");")

        
class _ConvertAlwaysVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        w = node.code.nodes[-1]
        assert isinstance(w.body.nodes[0], astNode.Yield)
        sl = w.body.nodes[0].value
        self.write("always @(")
        self.visit(sl, YIELD)
        self.write(") begin: %s" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        assert isinstance(w.body, astNode.Stmt)
        for stmt in w.body.nodes[1:]:
            self.writeline()
            self.visit(stmt)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)
        
    
class _ConvertInitialVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("initial begin: %s" % self.ast.name) 
        self.indent()
        self.writeDeclarations()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)


class _ConvertAlwaysCombVisitor(_ConvertVisitor):
    
    def __init__(self, ast, blockBuf, funcBuf):
        _ConvertVisitor.__init__(self, ast, blockBuf)
        self.funcBuf = funcBuf

    def visitFunction(self, node, *args):
        self.write("always @(")
        assert self.ast.senslist
        for s in self.ast.senslist[:-1]:
            self.write(s._name)
            self.write(', ')
        self.write(self.ast.senslist[-1]._name)
        self.write(") begin: %s" % self.ast.name)
        self.indent()
        self.writeDeclarations()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline(2)
        
    
class _ConvertFunctionVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnObj = ast.returnObj
        self.returnLabel = Label("RETURN")

    def writeOutputDeclaration(self):
        obj = self.ast.returnObj
        self.writeDeclaration(obj, self.ast.name, dir='')

    def writeInputDeclarations(self):
        for name in self.ast.argnames:
            obj = self.ast.symdict[name]
            self.writeline()
            self.writeDeclaration(obj, name, "input")
            
    def visitFunction(self, node, *args):
        self.write("function ")
        self.writeOutputDeclaration()
        self.indent()
        self.writeInputDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endfunction")
        self.writeline(2)

    def visitReturn(self, node, *args):
        self.write("%s = " % self.ast.name)
        self.visit(node.value)
        self.write(";")
        self.writeline()
        self.write("disable %s;" % self.returnLabel)
    
    
class _ConvertTaskVisitor(_ConvertVisitor):
    
    def __init__(self, ast, funcBuf):
        _ConvertVisitor.__init__(self, ast, funcBuf)
        self.returnLabel = Label("RETURN")

    def writeInterfaceDeclarations(self):
        for name in self.ast.argnames:
            obj = self.ast.symdict[name]
            output = name in self.ast.outputs
            input = name in self.ast.inputs
            inout = input and output
            dir = (inout and "inout") or (output and "output") or "input"
            self.writeline()
            self.writeDeclaration(obj, name, dir)
            
    def visitFunction(self, node, *args):
        self.write("task %s;" % self.ast.name)
        self.indent()
        self.writeInterfaceDeclarations()
        self.writeDeclarations()
        self.dedent()
        self.writeline()
        self.write("begin: %s" % self.returnLabel)
        self.indent()
        self.visit(node.code)
        self.dedent()
        self.writeline()
        self.write("end")
        self.writeline()
        self.write("endtask")
        self.writeline(2)
