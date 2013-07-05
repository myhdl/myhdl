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
