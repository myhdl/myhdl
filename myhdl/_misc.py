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

""" MyHDL miscellaneous public objects.

This module provides the following public myhdl objects:
instances -- function that returns instances in a generator function
downrange -- function that returns a downward range

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
import inspect

from types import GeneratorType
from sets import Set
from types import GeneratorType, ListType, TupleType

from myhdl._Cosimulation import Cosimulation
from myhdl._always_comb import _AlwaysComb
from myhdl._always import _Always
      
def _isGenSeq(obj):
    if isinstance(obj, (GeneratorType, Cosimulation, _AlwaysComb, _Always)):
        return True
    if not isinstance(obj, (ListType, TupleType, Set)):
        return False
##     if not obj:
##         return False
    for e in obj:
        if not _isGenSeq(e):
            return False
    return True

    
def instances():
    f = inspect.currentframe()
    d = inspect.getouterframes(f)[1][0].f_locals
    l = []
    for v in d.values():
      if _isGenSeq(v):
         l.append(v)
    return l
    
def downrange(start, stop=0, step=1):
    """ Return a downward range. """
    return range(start-1, stop-1, -step)
