import inspect
import ast
from myhdl._util import _dedent

def _makeAST(f):
    s = inspect.getsource(f)
    s = _dedent(s)
    tree = ast.parse(s)
    tree.sourcefile = inspect.getsourcefile(f)
    tree.lineoffset = inspect.getsourcelines(f)[1]-1
    return tree

def _genfunc(gen):
    from myhdl._always_comb import _AlwaysComb
    from myhdl._always_seq import _AlwaysSeq
    from myhdl._always import _Always
    if isinstance(gen, (_AlwaysComb, _AlwaysSeq, _Always)):
        func = gen.func
    else:
        func = gen.genfunc
    return func
