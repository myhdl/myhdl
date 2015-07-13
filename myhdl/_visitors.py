import ast

from myhdl import intbv
from myhdl._Signal import _Signal, _isListOfSigs


class _SigNameVisitor(ast.NodeVisitor):
    def __init__(self, symdict):
        self.toplevel = 1
        self.symdict = symdict
        self.results = {
            'input': set(),
            'output': set(),
            'inout': set(),
            'embedded_func': set()
        }
        self.context = 'input'

    def visit_Module(self, node):
        inputs = self.results['input']
        outputs = self.results['output']
        for n in node.body:
            self.visit(n)

    def visit_FunctionDef(self, node):
        if self.toplevel:
            self.toplevel = 0  # skip embedded functions
            for n in node.body:
                self.visit(n)
        else:
            self.results['embedded_func'] = node.name

    def visit_If(self, node):
        if not node.orelse:
            if isinstance(node.test, ast.Name) and \
               node.test.id == '__debug__':
                return  # skip
        self.generic_visit(node)

    def visit_Name(self, node):
        id = node.id
        if id not in self.symdict:
            return
        s = self.symdict[id]
        if isinstance(s, (_Signal, intbv)) or _isListOfSigs(s):
            if self.context in ('input', 'output', 'inout'):
                self.results[self.context].add(id)
            else:
                print(self.context)
                raise AssertionError("bug in always_comb")

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

    def visit_Subscript(self, node, access='input'):
        self.visit(node.value)
        self.context = 'input'
        self.visit(node.slice)

    def visit_AugAssign(self, node, access='input'):
        self.context = 'inout'
        self.visit(node.target)
        self.context = 'input'
        self.visit(node.value)

    def visit_ClassDef(self, node):
        pass # skip

    def visit_Exec(self, node):
        pass # skip

    def visit_Print(self, node):
        pass # skip
