from __future__ import absolute_import
import ast

from myhdl._util import _flatten


class Data():
    pass


def _getCellVars(symdict, arg):
    gens = _flatten(arg)
    data = Data()
    data.symdict = symdict
    v = _GetCellVars(data)
    for gen in gens:
        v.visit(gen.ast)
    return list(data.objset)


class _GetCellVars(ast.NodeVisitor):

    def __init__(self, data):
        self.data = data
        self.data.objset = set()

    def visit_Name(self, node):

        if node.id in self.data.symdict:
            self.data.objset.add(node.id)

        self.generic_visit(node)
