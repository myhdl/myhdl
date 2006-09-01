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

class EnumType(object):
    def __init__(self):
        raise TypeError("class EnumType is only intended for type checking on subclasses")

class EnumItemType(object):
    def __init__(self):
        raise TypeError("class EnumItemType is only intended for type checking on subclasses")


def enum(*args, **kwargs):

    # args = args
    encoding = kwargs.get('encoding', 'binary')
    argdict = {}
    codedict = {}
    if encoding == "binary":
        nrbits = len(bin(len(args)-1))
    elif encoding in ("one_hot", "one_cold"):
        nrbits = len(args)
    else:
        raise ValueError("Unsupported enum encoding: %s \n    Supported encodings:" + \
                         "    'binary', 'one_hot', 'one_cold'" % encoding)
    
    i = 0
    for arg in args:
        if not isinstance(arg, StringType):
            raise TypeError()
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
       
    class EnumItem(EnumItemType):
        def __init__(self, index, arg, type):
            self._index = index
            self._name = arg
            self._val = codedict[arg]
            self._nrbits = nrbits
            self._nritems = len(args)
            self._type = type
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
        def _toVHDL(self):
            return self._name

    class Enum(EnumType):
        def __init__(self):
            for index, slot in enumerate(args):
                self.__dict__[slot] = EnumItem(index, slot, self)
            self.__dict__['_nrbits'] = nrbits
            self.__dict__['_declared'] = False
        def __setattr__(self, attr, val):
            raise AttributeError("Cannot assign to enum attributes")
        def __len__(self):
            return len(args)
        def __repr__(self):
            return "<Enum: %s>" % ", ".join(args)
        __str__ = __repr__
        def _isDeclared(self):
            return self._declared
        def _setDeclared(self):
            self.__dict__['_declared'] = True
        def _clearDeclared(self):
            self.__dict__['_declared'] = False
        _toVHDL = __str__
        def _toVHDL(self, name):
            typename = "t_enum_%s" % name
            self.__dict__['_name'] = typename
            # XXX name generation
            str = "type %s is (\n    " % typename
            str += ",\n    ".join(args)         
            str += "\n);"
            return str
            
        
    return Enum()




    
        
