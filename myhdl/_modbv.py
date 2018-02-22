#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2011 Jan Decaluwe
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

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module with the modbv class """
from __future__ import absolute_import

from ._intbv import intbv
from ._compat import long


class modbv(intbv):
    __slots__ = []

    def _handleBounds(self):
        lo, hi, val = self._min, self._max, self._val
        if lo is not None:
            if val < lo or val >= hi:
                self._val = (val - lo) % (hi - lo) + lo

    def __repr__(self):
        return "modbv(" + repr(self._val) + ")"

    # indexing and slicing methods
    # dedicated for modbv to support "declaration by slicing"

    def __getitem__(self, key):
        if isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None:  # default
                j = 0
            j = int(j)
            if j < 0:
                raise ValueError("modbv[i:j] requires j >= 0\n"
                                 "            j == %s" % j)
            if i is None:  # default
                return modbv(self._val >> j)
            i = int(i)
            if i <= j:
                raise ValueError("modbv[i:j] requires i > j\n"
                                 "            i, j == %s, %s" % (i, j))
            res = modbv((self._val & (long(1) << i) - 1) >> j, _nrbits=i - j)
            return res
        else:
            i = int(key)
            res = bool((self._val >> i) & 0x1)
            return res
