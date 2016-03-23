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

""" module with the bin function.

"""
from myhdl._compat import long


def _int2bitstring(num):
    if num == 0:
        return '0'
    if abs(num) == 1:
        return '1'
    bits = []
    p, q = divmod(num, 2)
    bits.append(str(q))
    while not (abs(p) == 1):
        p, q = divmod(p, 2)
        bits.append(str(q))
    bits.append('1')
    bits.reverse()
    return ''.join(bits)


def bin(num, width=0):
    """Return a binary string representation.

    num -- number to convert
    Optional parameter:
    width -- specifies the desired string (sign bit padding)
    """
    num = long(num)
    s = _int2bitstring(num)
    if width:
        pad = '0'
        if num < 0:
            pad = '1'
        return (width - len(s)) * pad + s
    return s
