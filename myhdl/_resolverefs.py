from __future__ import absolute_import
import ast
import itertools
from types import FunctionType

from myhdl._util import _flatten, _makeAST, _genfunc
from myhdl._enum import EnumType
from myhdl._Signal import SignalType


class Data():
    pass


def _resolveRefs(symdict, arg):
    gens = _flatten(arg)
    data = Data()
    data.symdict = symdict
    v = _AttrRefTransformer(data)
    for gen in gens:
        func = _genfunc(gen)
        tree = _makeAST(func)
        v.visit(tree)
    return data.objlist

#TODO: Refactor this into two separate nodetransformers, since _resolveRefs
#needs only the names, not the objects

def _suffixer(name):
    suffixed_names = (name+'_renamed{0}'.format(i) for i in itertools.count())
    return itertools.chain([name], suffixed_names)


class _AttrRefTransformer(ast.NodeTransformer):
    def __init__(self, data):
        self.data = data
        self.data.objlist = []
        self.myhdl_types = (EnumType, SignalType)

    def visit_Attribute(self, node):
        self.generic_visit(node)

        reserved = ('next',  'posedge',  'negedge',  'max',  'min',  'val',  'signed')
        if node.attr in reserved:
            return node

        #Don't handle subscripts for now.
        if not isinstance(node.value, ast.Name):
            return node

        obj = self.data.symdict[node.value.id]
        #Don't handle enums and functions, handle signals as long as it is a new attribute
        if isinstance(obj, (EnumType, FunctionType)):
            return node
        elif isinstance(obj, SignalType):
            if hasattr(SignalType, node.attr):
                return node

        attrobj = getattr(obj, node.attr)

        name = node.value.id + '_' + node.attr
        new_name = next(s for s in _suffixer(name) if s not in self.data.symdict)
        self.data.symdict[new_name] = attrobj
        self.data.objlist.append(new_name)

        new_node = ast.Name(id=new_name, ctx=node.value.ctx)
        return ast.copy_location(new_node, node)

    def visit_FunctionDef(self, node):
        nodes = _flatten(node.body, node.args)
        for n in nodes:
            self.visit(n)
        return node
