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

""" myhdl utilility objects.

This module provides the following myhdl objects:
downrange -- function that returns a downward range
bin -- returns a binary string representation.
       The optional width specifies the desired string
       width: padding of the sign-bit is used.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import exceptions
import sys
import inspect
import re
from sets import Set
from types import FunctionType, GeneratorType, ListType, TupleType
import compiler
# hope this will always work ...
from compiler.consts import CO_GENERATOR


def downrange(start, stop=0, step=1):
    """ Return a downward range. """
    return range(start-1, stop-1, -step)
        
## class StopSimulation(exceptions.Exception):
##     """ Basic exception to stop a Simulation """
##     pass

## class SuspendSimulation(exceptions.Exception):
##     """ Basic exception to suspend a Simulation """
##     pass

def _printExcInfo():
    kind, value  = sys.exc_info()[:2]
    msg = str(kind)
    # msg = msg[msg.rindex('.')+1:]
    if str(value):
        msg += ": %s" % value
        print >> sys.stderr, msg

def _isGenFunc(obj):
    if isinstance(obj, FunctionType):
        return bool(obj.func_code.co_flags & CO_GENERATOR)
    return bool(0)

def _flatten(*args):
    arglist = []
    for arg in args:
        if isinstance(arg, (list, tuple, Set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist

