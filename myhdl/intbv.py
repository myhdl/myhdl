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

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module with the intbv class """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"


import sys
maxint = sys.maxint
from types import StringType
import operator

from bin import bin

from __builtin__ import max as maxfunc

class intbv(object):
    __slots__ = ('_val', '_min', '_max', '_len', '_nrbits')
    
    def __init__(self, val=0, min=None, max=None, _len=0):
        self._len = _len
        nrbits = 0
        if _len:
            self._min = 0
            self._max = 2**_len
            nrbits = _len
        else:
            self._min = min
            if min is not None:
                nrbits = len(bin(min))
            self._max = max
            if max is not None:
                n = len(bin(max))
                if n > nrbits:
                    nrbits = n
        self._nrbits = nrbits
        if isinstance(val, (int, long)):
            self._val = val
        elif type(val) is StringType:
            self._val = long(val, 2)
            self._len = len(val)
        elif isinstance(val, intbv):
            self._val = val._val
        else:
            raise TypeError("intbv constructor arg should be int or string")
        self._checkBounds()

    def _checkBounds(self):
        if self._max is not None:
            if self._val >= self._max:
                raise ValueError("intbv value %s >= maximum %s" %
                                 (self._val, self._max))
        if self._min is not None:
            if self._val < self._min:
                raise ValueError("intbv value %s < minimum %s" %
                                 (self._val, self._min))

    # concat method
    def concat(self, *args):
        v = self._val
        basewidth = width = self._len
        for a in args:
            if type(a) is intbv:
                w = a._len
                if not w:
                    raise TypeError, "intbv arg to concat should have length"
                else:
                    v = v * (2**w) + a._val
                    width += w
            elif type(a) is StringType:
                w = len(a)
                v= v*(2**w) + long(a, 2)
                width += w
            else:
                raise TypeError
        if basewidth:
            return intbv(v, _len=basewidth + width)
        else:
            return intbv(v)

    # hash
    def __hash__(self):
        return hash(self._val)
        
    # copy methods
    def __copy__(self):
        return intbv(self._val)
    def __deepcopy__(self, visit):
        return intbv(self._val)

    # iterator method
    def __iter__(self):
        if not self._len:
            raise TypeError, "Cannot iterate over unsized intbv"
        return iter([self[i] for i in range(self._len, -1, -1)])

    # logical testing
    def __nonzero__(self):
        if self._val:
            return 1
        else:
            return 0

    # indexing and slicing methods

    def __getitem__(self, i):
        res = intbv((self._val >> i) & 0x1, _len=1)
        return res

    def __getslice__(self, i, j):
        if j == maxint: # default
            j = 0
        if j < 0:
            raise ValueError, "intbv[i:j] requires j >= 0\n" \
                  "            j == %s" % j
        if i == 0: # default
            return intbv(self._val >> j)
        if i <= j:
            raise ValueError, "intbv[i:j] requires i > j\n" \
                  "            i, j == %s, %s" % (i, j)
        res = intbv((self._val & 2**i-1) >> j, _len=i-j)
        return res
        
    def __setitem__(self, i, val):
        if val not in (0, 1):
            raise ValueError, "intbv[i] = v requires v in (0, 1)\n" \
                  "            i == %s " % i
        if val:
            self._val |= (2**i)
        else:
            self._val &= ~(2**i)

    def __setslice__(self, i, j, val):
        if j == maxint: # default
            j = 0
        if j < 0:
            raise ValueError, "intbv[i:j] = v requires j >= 0\n" \
                  "            j == %s" % j
        if i == 0: # default
            q = self._val % (2**j)
            self._val = val * 2**j + q
            self._checkBounds()
            return
        if i <= j:
            raise ValueError, "intbv[i:j] = v requires i > j\n" \
                  "            i, j, v == %s, %s, %s" % (i, j, val)
        if val >= 2**(i-j) or val < -2**(i-j):
            raise ValueError, "intbv[i:j] = v abs(v) too large\n" \
                  "            i, j, v == %s, %s, %s" % (i, j, val)
        mask = (2**(i-j))-1
        mask *= 2**j
        self._val &= ~mask
        self._val |= val * 2**j
        self._checkBounds()
              
        
    # integer-like methods
    
    def __add__(self, other):
        if isinstance(other, intbv):
            return self._val + other._val
        else:
            return self._val + other
    def __radd__(self, other):
        return other + self._val
    
    def __sub__(self, other):
        if isinstance(other, intbv):
            return self._val - other._val
        else:
            return self._val - other
    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if isinstance(other, intbv):
            return self._val * other._val
        else:
            return self._val * other
    def __rmul__(self, other):
        return other * self._val

    def __div__(self, other):
        if isinstance(other, intbv):
            return self._val / other._val
        else:
            return self._val / other
    def __rdiv__(self, other):
        return other / self._val
    
    def __truediv__(self, other):
        if isinstance(other, intbv):
            return operator.truediv(self._val, other._val)
        else:
            return operator.truediv(self._val, other)
    def __rtruediv__(self, other):
        return operator.truediv(other, self._val)
    
    def __floordiv__(self, other):
        if isinstance(other, intbv):
            return self._val // other._val
        else:
            return self._val // other
    def __rfloordiv__(self, other):
        return other //  self._val
    
    def __mod__(self, other):
        if isinstance(other, intbv):
            return self._val % other._val
        else:
            return self._val % other
    def __rmod__(self, other):
        return other % self._val

    # divmod
    
    def __pow__(self, other):
        if isinstance(other, intbv):
            return self._val ** other._val
        else:
            return self._val ** other
    def __rpow__(self, other):
        return other ** self._val

    def __lshift__(self, other):
        if isinstance(other, intbv):
            return self._val << other._val
        else:
            return self._val << other
    def __rlshift__(self, other):
        return other << self._val
            
    def __rshift__(self, other):
        if isinstance(other, intbv):
            return self._val >> other._val
        else:
            return self._val >> other
    def __rrshift__(self, other):
        return other >> self._val
           
    def __and__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val & other._val, _len=max(self._len, other._len))
        else:
            return intbv(self._val & other, _len=self._len)
    def __rand__(self, other):
        return intbv(other & self._val, _len=self._len)

    def __or__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val | other._val, _len=max(self._len, other._len))
        else:
            return intbv(self._val | other, _len=self._len)
    def __ror__(self, other):
        return intbv(other | self._val, _len=self._len)
    
    def __xor__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val ^ other._val, _len=max(self._len, other._len))
        else:
            return intbv(self._val ^ other, _len=self._len)
    def __rxor__(self, other):
        return intbv(other ^ self._val, _len=self._len)

    def __iadd__(self, other):
        if isinstance(other, intbv):
            self._val += other._val
        else:
            self._val += other
        self._checkBounds()
        return self
        
    def __isub__(self, other):
        if isinstance(other, intbv):
            self._val -= other._val
        else:
            self._val -= other
        self._checkBounds()
        return self
        
    def __imul__(self, other):
        if isinstance(other, intbv):
            self._val *= other._val
        else:
            self._val *= other
        self._checkBounds()
        return self
    
    def __ifloordiv__(self, other):
        if isinstance(other, intbv):
            self._val //= other._val
        else:
            self._val //= other
        self._checkBounds()
        return self

    def __idiv__(self, other):
        raise TypeError("intbv: Augmented classic division not supported")
    def __itruediv__(self, other):
        raise TypeError("intbv: Augmented true division not supported")
    
    def __imod__(self, other):
        if isinstance(other, intbv):
            self._val %= other._val
        else:
            self._val %= other
        self._checkBounds()
        return self
        
    def __ipow__(self, other, modulo=None):
        # XXX why 3rd param required?
        # unused but needed in 2.2, not in 2.3 
        if isinstance(other, intbv):
            self._val **= other._val
        else:
            self._val **= other
        if not isinstance(self._val, (int, long)):
            raise ValueError("intbv value should be integer")
        self._checkBounds()
        return self
        
    def __iand__(self, other):
        if isinstance(other, intbv):
            self._val &= other._val
        else:
            self._val &= other
        self._checkBounds()
        return self

    def __ior__(self, other):
        if isinstance(other, intbv):
            self._val |= other._val
        else:
            self._val |= other
        self._checkBounds()
        return self

    def __ixor__(self, other):
        if isinstance(other, intbv):
            self._val ^= other._val
        else:
            self._val ^= other
        self._checkBounds()
        return self

    def __ilshift__(self, other):
        if isinstance(other, intbv):
            self._val <<= other._val
        else:
            self._val <<= other
        self._checkBounds()
        return self

    def __irshift__(self, other):
        if isinstance(other, intbv):
            self._val >>= other._val
        else:
            self._val >>= other
        self._checkBounds()
        return self

    def __neg__(self):
        return -self._val

    def __pos__(self):
        return +self._val

    def __abs__(self):
        return abs(self._val)

    def __invert__(self):
        if self._len:
            return intbv(~self._val & (2**self._len)-1)
        else:
            return intbv(~self._val)
    
    def __int__(self):
        return int(self._val)
        
    def __long__(self):
        return long(self._val)

    def __float__(self):
        return float(self._val)

    # XXX __complex__ seems redundant ??? (complex() works as such?)
    
    def __oct__(self):
        return oct(self._val)
    
    def __hex__(self):
        return hex(self._val)
      
        
    def __cmp__(self, other):
        if isinstance(other, intbv):
            return cmp(self._val, other._val)
        else:
            return cmp(self._val, other)

    # representation 
    def __str__(self):
        return str(self._val)

    def __repr__(self):
        return "intbv(" + repr(self._val) + ")"
 
