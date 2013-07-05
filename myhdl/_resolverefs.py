import ast
from myhdl._convutils import _makeAST
from myhdl._util import _flatten


class Data():
    pass


def _resolveRefs(symdict, arg):
    #temporary hack to prevent circular dependencies
    from myhdl._always_comb import _AlwaysComb
    from myhdl._always_seq import _AlwaysSeq
    from myhdl._always import _Always
    gens = _flatten(arg)
    data = Data()
    data.symdict = symdict
    v = _AttrRefTransformer(data)
    for gen in gens:
        if isinstance(gen, (_AlwaysComb, _AlwaysSeq, _Always)):
            func = gen.func
        else:
            func = gen.gen.gi_frame
        tree = _makeAST(func)
        v.visit(tree)
    return data.objlist


class _AttrRefTransformer(ast.NodeTransformer):
    def __init__(self, data):
        self.data = data
        self.data.objlist = []

    def visit_Attribute(self, node):
        reserved = ('next', 'posedge', 'negedge', 'max', 'min', 'val', 'signed')
        self.generic_visit(node)
        if node.attr in reserved:
            return node
        else:
            obj = self.data.symdict[node.value.id]
            attrobj = getattr(obj, node.attr)
            new_name = node.value.id+'.'+node.attr
            if new_name not in self.data.symdict:
                self.data.symdict[new_name] = attrobj
                self.data.objlist.append(new_name)
            else:
                pass
                #assert self.data.symdict[new_name] == attrobj
            new_node = ast.Name(id=new_name, ctx=node.value.ctx)
            return ast.copy_location(new_node, node)

    def visit_FunctionDef(self, node):
        nodes = _flatten(node.body, node.args)
        for n in nodes:
            self.visit(n)
        return node
