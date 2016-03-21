#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
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

# pylint: disable=redefined-builtin

""" module with the concat function.

"""
from __future__ import absolute_import

from myhdl._compat import integer_types
from myhdl._intbv import intbv
from myhdl._Signal import _Signal
from myhdl._compat import long


def concat(base, *args):

    if isinstance(base, intbv):
        basewidth = base._nrbits
        val = base._val
    elif isinstance(base, integer_types):
        if isinstance(base, bool):
            basewidth = 1
        else:
            basewidth = 0
        val = base
    elif isinstance(base, _Signal):
        basewidth = base._nrbits
        if isinstance(base._val, intbv):
            val = base._val._val
        else:
            val = base._val
    elif isinstance(base, str):
        basewidth = len(base)
        val = long(base, 2)
    else:
        raise TypeError("concat: inappropriate first argument type: %s"
                        % type(base))

    width = 0
    for i, arg in enumerate(args):
        if isinstance(arg, intbv):
            w = arg._nrbits
            v = arg._val
        elif isinstance(arg, _Signal):
            w = arg._nrbits
            if isinstance(arg._val, intbv):
                v = arg._val._val
            else:
                v = arg._val
        elif isinstance(arg, bool):
            w = 1
            v = arg
        elif isinstance(arg, str):
            w = len(arg)
            v = long(arg, 2)
        else:
            raise TypeError("concat: inappropriate argument type: %s"
                            % type(arg))
        if not w:
            raise TypeError("concat: arg on pos %d should have length" % (i + 1))
        width += w
        val = val << w | v & (long(1) << w) - 1

    if basewidth:
        return intbv(val, _nrbits=basewidth + width)
    else:
        return intbv(val)
