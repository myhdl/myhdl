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

""" myhdl miscellaneous objects.

This module provides the following myhdl objects:
instances -- function that returns instances in a generator function
             these are all generators in the local namespace
processes -- function that returns processes in a generator function
             these are generators obtained by calling local generator functions

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import sys
import inspect

from types import GeneratorType

from myhdl import Cosimulation
from myhdl._util import _isgeneratorfunction, _isGenSeq

    
def instances():
    f = inspect.currentframe()
    d = inspect.getouterframes(f)[1][0].f_locals
    l = []
    for v in d.values():
      if type(v) in (GeneratorType, Cosimulation):
         l.append(v)
      elif _isGenSeq(v):
         l.append(v)
    return l
    
     
def processes():
    f = inspect.currentframe()
    d = inspect.getouterframes(f)[1][0].f_locals
    l = []
    for v in d.values():
      if _isgeneratorfunction(v):
         l.append(v()) # call it
    return l
