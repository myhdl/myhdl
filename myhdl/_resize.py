#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2013 Christopher L. Felton
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

""" Module with the fixbv resize function """


import math
from _fixbv import fixbv
from _fixbv import FixedPointFormat

                  # round    :
ROUND_MODES = (   # towards  :
    'ceil',       # +infinity: always round up
    'fix',        # 0        : always down
    'floor',      # -infinity: truncate, always round down
    'nearest',    # nearest  : tie towards largest absolute value
    'round',      # nearest  : ties to +infinity
    'convergent', # nearest  : tie to closest even (round_even)
    'round_even', # nearest  : tie to closest even (convergent)
    )

OVERFLOW_MODES = (
    'saturate',
    'ring',
    'wrap',
    )


def is_round_mode(mode):
    if mode.lower() in ROUND_MODES:
       found = True
    else:
        # @todo: is there a close match?
        found = False        
    return found


def is_overflow_mode(mode):
    if mode.lower() in OVERFLOW_MODES:
        found = True
    else:
        # @todo: is there a close match?
        found = False
    return found


def _overflow(val, fmt, overflow_mode):
    """handle overflow"""

    assert is_overflow_mode(overflow_mode)
    wl,iwl,fwl = fmt
    mm = 2**(wl-1)
    mmin,mmax = -mm,mm
    #print("    [rsz][ovl]: %f %d %d, %s" % (val, mmin, mmax, fmt))

    if overflow_mode == 'saturate':
        if val >= mmax:
            retval = mmax-1
        elif val <= mmin:
            retval = mmin
        else:
            retval = val
    elif overflow_mode == 'ring' or overflow_mode == 'wrap':
        retval = (val - mmin) % (mmax - mmin) + mmin
    else:
        raise ValueError

    return retval


def _round(val, fmt, round_mode):
    """Round the initial value if needed"""
    # Scale the value to the integer range (the underlying representation)

    assert is_round_mode(round_mode)
    assert isinstance(fmt, tuple)
    wl,iwl,fwl = fmt
    _val = val
    val = val * 2.0**fwl
    #print("    [rsz][rnd]: %f %f, %s" % (val, _val, fmt))

    if round_mode == 'ceil':
        retval = math.ceil(val)

    elif round_mode == 'fix':
        if val > 0:
            retval = math.floor(val)
        else:
            retval = math.ceil(val)

    elif round_mode == 'floor':
        retval = math.floor(val)

    elif round_mode == 'nearest':
        fval,ival = math.modf(val)
        if fval == .5:
            retval = int(val+1) if val > 0 else int(val-1)
        else:
            retval = round(val)

    elif round_mode == 'round':
        retval = round(val)
        
    elif round_mode == 'round_even' or round_mode == 'convergent':
        fval,ival = math.modf(val)
        abs_ival = int(abs(ival))
        sign = -1 if ival < 0 else 1

        if (abs(fval) - 0.5) == 0.0:
            if abs_ival%2 == 0:
                retval = abs_ival * sign
            else:
                retval = (abs_ival + 1) * sign
        else:
            retval = round(val)

    else:
        raise TypeError("invalid round mode!" % self.round_mode)

    return int(retval)


def resize(val, fmt, round_mode='convergent', overflow_mode='saturate'):
    """
    """

    if isinstance(fmt, fixbv):
        fmt = fmt.format
    elif isinstance(fmt, FixedPointFormat):
        fmt = tupel(fmt[:])
    elif isinstance(fmt, tuple):
        fmt = fmt
    else:
        pass

    if isinstance(val, fixbv):
        fval = float(val)
    elif isinstance(val, float):
        fval = val
    else:
        pass
        
    wl,iwl,fwl = fmt
    mm = 2**iwl
    res = 2**-fwl
    rfx = fixbv(0, min=-mm, max=mm, res=res)
    assert (wl,iwl,fwl,) == rfx.format, "%d,%d,%d != %s" % (wl,iwl,fwl, repr(rfx))

    ival = _round(fval, fmt, round_mode=round_mode)
    ival = _overflow(ival, fmt, overflow_mode=overflow_mode)
    rfx._val = ival
    rfx._handleBounds()                     

    return rfx

    
        