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

""" Module that implements enum.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from types import StringType

from myhdl._bin import bin

def enum(*args, **kwargs):

    # args = args
    encoding = kwargs.get('encoding', 'binary')
    argdict = {}
    codedict = {}
    if encoding == "binary":
        nrbits = len(bin(len(args)))
    elif encoding in ("one_hot", "one_cold"):
        nrbits = len(args)
    else:
        raise ValueError("Unsupported enum encoding: %s \n    Supported encodings:" + \
                         "    'binary', 'one_hot', 'one_cold'" % encoding)
    
    i = 0
    for arg in args:
        if type(arg) is not StringType:
            raise TypeError
        if codedict.has_key(arg):
            raise ValueError("enum literals should be unique")
        argdict[i] = arg
        if encoding == "binary":
            code = bin(i, nrbits)
        elif encoding == "one_hot":
            code = bin(1<<i, nrbits)
        else: # one_cold
            code = bin(~(1<<i), nrbits)
        if len(code) > nrbits:
            code = code[-nrbits:]
        codedict[arg] = code
        i += 1
       
    class EnumItem(object):
        def __init__(self, index, arg):
            self._index = index
            self._val = codedict[arg]
            self._nrbits = nrbits
            self._nritems = len(args)
        def __repr__(self):
            return argdict[self._index]
        def __hex__(self):
            return hex(int(self._val, 2))
        __str__ = __repr__
        def _toVerilog(self, dontcare=False):
            val = self._val
            if dontcare:
                if encoding == "one_hot":
                    val = val.replace('0', '?')
                elif encoding == "one_cold":
                    val = val.replace('1', '?')
            return "%d'b%s" % (self._nrbits, val)

    class Enum(object):
        def __init__(self):
            for index, slot in enumerate(args):
                self.__dict__[slot] = EnumItem(index, slot)
            self.__dict__['_nrbits'] = nrbits
        def __setattr__(self, attr, val):
            raise AttributeError("Cannot assign to enum attributes")
        def __len__(self):
            return len(args)
        def __repr__(self):
            return "<Enum: %s>" % ", ".join(args)
        __str__ = __repr__
        
    return Enum()




    
        
