#pylint: disable=invalid-name

import ast

from myhdl._intbv import intbv
from myhdl._Signal import _Signal, _isListOfSigs


class _SigNameVisitor(ast.NodeVisitor):

    def __init__(self, symdict):
        self.toplevel = 1
        self.symdict = symdict
        self.inputs = set()
        self.outputs = set()
        self.inouts = set()
        self.embedded_func = None
        self.context = 'input'
        self.sigdict = {}
        self.losdict = {}

    def visit_Module(self, node):
        for n in node.body:
            self.visit(n)

    def visit_FunctionDef(self, node):
        if self.toplevel:
            self.toplevel = 0  # skip embedded functions
            for n in node.body:
                self.visit(n)
        else:
            self.embedded_func = node.name

    def visit_If(self, node):
        if not node.orelse:
            if isinstance(node.test, ast.Name) and \
                    node.test.id == '__debug__':
                return  # skip
        self.generic_visit(node)

    def visit_Name(self, node):
        n = node.id
        if n not in self.symdict:
            return
        s = self.symdict[n]
        if isinstance(s, (_Signal, intbv)) or _isListOfSigs(s):
            if self.context == 'input':
                self.inputs.add(n)
            elif self.context == 'output':
                self.outputs.add(n)
            elif self.context == 'inout':
                self.inouts.add(n)
            elif self.context == 'pass':
                pass
            else:
                print(self.context)
                raise AssertionError("bug in _SigNameVisitor")
        if isinstance(s, _Signal):
            self.sigdict[n] = s
        elif _isListOfSigs(s):
            self.losdict[n] = s

    def visit_Assign(self, node):
        self.context = 'output'
        for n in node.targets:
            self.visit(n)
        self.context = 'input'
        self.visit(node.value)

    def visit_Attribute(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        fn = None
        if isinstance(node.func, ast.Name):
            fn = node.func.id
        if fn == "len":
            pass
        else:
            self.generic_visit(node)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.context = 'input'
        self.visit(node.slice)

    def visit_AugAssign(self, node):
        self.context = 'inout'
        self.visit(node.target)
        self.context = 'input'
        self.visit(node.value)

    def visit_ClassDef(self, node):
        pass  # skip

    def visit_Exec(self, node):
        pass  # skip

    def visit_Print(self, node):
        self.context = 'pass'
        self.generic_visit(node)
        self.context == 'input'
