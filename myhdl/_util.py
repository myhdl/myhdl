#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2009 Jan Decaluwe
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

""" Module with utilility objects for MyHDL.

"""
from __future__ import absolute_import
from __future__ import print_function

import __future__
import ast
import sys
import inspect

from tokenize import generate_tokens, untokenize, INDENT

from myhdl._compat import integer_types, StringIO


def _printExcInfo():
    kind, value = sys.exc_info()[:2]
    msg = str(kind)
    # msg = msg[msg.rindex('.')+1:]
    if str(value):
        msg += ": %s" % value
        print(msg, file=sys.stderr)

_isGenFunc = inspect.isgeneratorfunction


def _flatten(*args):
    arglist = []
    for arg in args:
        if isinstance(arg, (list, tuple, set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist


def _isTupleOfInts(obj):
    if not isinstance(obj, tuple):
        return False
    for e in obj:
        if not isinstance(e, integer_types):
            return False
    return True


def _dedent(s):
    """Dedent python code string."""

    result = [t[:2] for t in generate_tokens(StringIO(s).readline)]
    # set initial indent to 0 if any
    if result[0][0] == INDENT:
        result[0] = (INDENT, '')
    return untokenize(result)


def _makeAST(f):
    # Need to look at the flags used to compile the original function f and
    # pass these same flags to the compile() function. This ensures that
    # syntax-changing __future__ imports like print_function work correctly.
    orig_f_co_flags = f.__code__.co_flags
    # co_flags can contain various internal flags that we can't pass to
    # compile(), so strip them out here
    valid_flags = 0
    for future_feature in __future__.all_feature_names:
        feature = getattr(__future__, future_feature)
        valid_flags |= feature.compiler_flag
    s = inspect.getsource(f)
    s = _dedent(s)
    # use compile instead of ast.parse so that additional flags can be passed
    flags = ast.PyCF_ONLY_AST | (orig_f_co_flags & valid_flags)
    tree = compile(s, filename='<unknown>', mode='exec',
        flags=flags, dont_inherit=True)
    # tree = ast.parse(s)
    tree.sourcefile = inspect.getsourcefile(f)
    tree.lineoffset = inspect.getsourcelines(f)[1] - 1
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
