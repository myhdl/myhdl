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
Error -- myhdl Error exception
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
from types import FunctionType, GeneratorType, ListType, TupleType

from myhdl import Cosimulation


def downrange(start, stop=0):
    """ Return a downward range. """
    return range(start-1, stop-1, -1)

def _int2bitstring(num):
    if num == 0:
        return '0'
    if abs(num) == 1:
        return '1'
    return _int2bitstring(num // 2) + _int2bitstring(num % 2)

def bin(num, width=0):
    """Return a binary string representation.

    num -- number to convert
    Optional parameter:
    width -- specifies the desired string (sign bit padding)
    """
    num = long(num)
    s = _int2bitstring(num)
    pad = '0'
    if num < 0:
        pad = '1'
    return (width - len(s)) * pad + s

class Error(Exception):
    pass
        
class StopSimulation(exceptions.Exception):
    """ Basic exception to stop a Simulation """
    pass

class SuspendSimulation(exceptions.Exception):
    """ Basic exception to suspend a Simulation """
    pass

def printExcInfo():
    kind, value  = sys.exc_info()[:2]
    msg = str(kind)
    msg = msg[msg.rindex('.')+1:]
    if str(value):
        msg += ": %s" % value
        print msg
       
def _isgeneratorfunction(obj):
   if type(obj) is FunctionType:
         s = inspect.getsource(obj)
         if re.search(r"\byield\b", s):
            return 1
   return 0

def _isGenSeq(obj):
    if type(obj) in (GeneratorType, Cosimulation):
        return 1
    if not isinstance(obj, (ListType, TupleType)):
        return 0
    for e in obj:
        if not _isGenSeq(e):
            return 0
    return 1
