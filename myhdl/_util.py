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


import exceptions
import sys
import inspect
import re
from types import FunctionType, GeneratorType, ListType, TupleType

from tokenize import generate_tokens, untokenize, INDENT
from cStringIO import StringIO


def _printExcInfo():
    kind, value  = sys.exc_info()[:2]
    msg = str(kind)
    # msg = msg[msg.rindex('.')+1:]
    if str(value):
        msg += ": %s" % value
        print >> sys.stderr, msg

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
        if not isinstance(e, (int, long)):
            return False
    return True

def _dedent(s):
    """Dedent python code string."""

    result = [t[:2] for t in generate_tokens(StringIO(s).readline)]
    # set initial indent to 0 if any
    if result[0][0] == INDENT:
        result[0] = (INDENT, '')
    return untokenize(result)
    


    
