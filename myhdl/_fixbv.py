#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2013 Jan Decaluwe
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
from __future__ import absolute_import, division
from math import floor
import operator

from myhdl._compat import long, integer_types, string_types, builtins
from myhdl._bin import bin
from myhdl._intbv import intbv

class fixbv(object):
    #__slots__ = ('_val', '_min', '_max', '_nrbits', '_handleBounds')
    
    def __init__(self, val, shift, min=None, max=None, _nrbits=0):
        if _nrbits:
            self._min = 0
            self._max = 2**_nrbits
        else:
            if isinstance(min, float):
                self._min = int(floor(min*2**(-shift) + 0.5))
            else:
                self._min = min
            if isinstance(max, float):
                self._max = int(floor(max*2**(-shift) + 0.5))
            else:
                self._max = max
            if self._max is not None and self._min is not None:
                if self._min >= 0:
                    _nrbits = len(bin(self._max-1))
                elif self._max <= 1:
                    _nrbits = len(bin(self._min))
                else:
                    # make sure there is a leading zero bit in positive numbers
                    _nrbits = builtins.max(len(bin(self._max-1))+1, len(bin(self._min)))
        if isinstance(val, float):
            self._val = int(floor(val*2**(-shift) + 0.5))
            self._shift = shift
        elif isinstance(val, integer_types):
            self._val = val
            self._shift = shift
        elif isinstance(val, string_types):
            mval = val.replace('_', '')
            self._val = long(mval, 2)
            _nrbits = len(mval)
            self._shift = shift
        elif isinstance(val, fixbv):
            self._val = val._val*2**(val._shift-shift)
            self._min = val._min
            self._max = val._max
            self._shift = val._shift
            _nrbits = val._nrbits
        elif isinstance(val, intbv):
            self._val = val._val
            self._min = val._min
            self._max = val._max
            self._shift = shift
            _nrbits = val._nrbits
        else:
            raise TypeError("fixbv constructor arg should be inbv, int or string")
        self._nrbits = _nrbits
        self._handleBounds()
        
    # support for the 'min' and 'max' attribute
    @property
    def max(self):
        return self._max

    @property
    def min(self):
        return self._min

    @property
    def shift(self):
        return self._shift

    #
    # function : _isfixbv
    # brief    : Check if the 'other' is a fixbv or a signal containing a fixbv, return true is this
    #            is the case
    #
    def _isfixbv(self, other):
        if isinstance(other, fixbv):
            return True
        if hasattr(other, '_val'):
            if isinstance(other._val, fixbv):
                return True
        return False
        
    #
    # function : align
    # brief    : Align the input variable "val" to the fixbv object. This
    #            function supports different input types:
    #            o fixbv
    #            o intbv
    #            o integer
    #            o float
    #
    def align(self, other):
        if isinstance(other, float):
            val = int(floor(other*2**-self.shift + 0.5))
        elif isinstance (other, integer_types):
            val = int(other*2**-self.shift)
        elif isinstance (other, intbv):
            val = other._val
        elif isinstance (other, fixbv):
            val = other._val*2**(other._shift-self.shift)
        else:
            TypeError("fixbv align arg should be float, int, intbv or fixbv")
        return val
            
    def _handleBounds(self):
        if self._max is not None:
            val = self._val*2**self._shift
            if val >= self._max:
                raise ValueError("fixbv value {} ({}) >= maximum {} ({})".format(
                    val, val*2**self._shift, self._max, self._max*2**self._shift))
        if self._min is not None:
            if val < self._min:
                raise ValueError("fixbv value %s < minimum %s" %
                                 (val, self._min))
                
    def _hasFullRange(self):
        min, max = self._min, self._max
        if max <= 0:
            return False
        if min not in (0, -max):
            return False
        return max & max-1 == 0


    # hash
    def __hash__(self):
        raise TypeError("fixbv objects are unhashable")
        
    # copy methods
    def __copy__(self):
        c = type(self)(self._val, self._shift)
        c._min = self._min
        c._max = self._max
        c._nrbits = self._nrbits
        return c

    def __deepcopy__(self, visit):
        c = type(self)(self._val, self._shift)
        c._min = self._min
        c._max = self._max
        c._nrbits = self._nrbits
        return c

    # iterator method
    def __iter__(self):
        if not self._nrbits:
            raise TypeError("Cannot iterate over unsized fixbv")
        return iter([self[i+self._shift] for i in range(self._nrbits-1, -1, -1)])

    # logical testing
    def __bool__(self):
        return bool(self._val)

    __nonzero__ = __bool__

    # length
    def __len__(self):
        return self._nrbits

    # indexing and slicing methods

    def __getitem__(self, key):
        if isinstance(key, slice):
            i, j = key.start-self._shift, key.stop-self._shift
            if j is None: # default
                j = self._shift
            j = int(j)
            if j < 0:
                raise ValueError("fixbv[i:j] requires j >= {}\n" \
                      "            j == {}".format(self._shift, j))
            if i is None: # default
                return intbv(self._val >> j)
            i = int(i)
            if i <= j:
                raise ValueError("fixbv[i:j] requires i > j\n" \
                      "            i, j == {}, {}".format(i, j))
            res = intbv((self._val & (long(1) << i)-1) >> j, _nrbits=i-j)
            return res
        else:
            i = int(key-self._shift)
            res = bool((self._val >> i) & 0x1)
            return res


       
    def __setitem__(self, key, val):
        # convert val to int to avoid confusion with intbv or Signals
        val = int(val)
        if isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None: # default
                j = 0
            j = int(j)
            if j < 0:
                raise ValueError("intbv[i:j] = v requires j >= 0\n" \
                      "            j == %s" % j)
            if i is None: # default
                q = self._val % (long(1) << j)
                self._val = val * (long(1) << j) + q
                self._handleBounds()
                return
            i = int(i)
            if i <= j:
                raise ValueError("intbv[i:j] = v requires i > j\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val))
            lim = (long(1) << (i-j))
            if val >= lim or val < -lim:
                raise ValueError("intbv[i:j] = v abs(v) too large\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val))
            mask = (lim-1) << j
            self._val &= ~mask
            self._val |= (val << j)
            self._handleBounds()
        else:
            i = int(key)
            if val == 1:
                self._val |= (long(1) << i)
            elif val == 0:
                self._val &= ~(long(1) << i)
            else:
                raise ValueError("intbv[i] = v requires v in (0, 1)\n" \
                      "            i == %s " % i)
               
            self._handleBounds()


        
    # integer-like methods
    
    def __add__(self, other):
        if self._isfixbv(other):
            if self._shift >= other._shift:
                val = self._val*2**(self._shift-other._shift) + other._val
                shift = other._shift
            else:
                val = self._val + other._val*2**(other._shift-self._shift) 
                shift = self._shift
            return fixbv(val, shift)
        elif isinstance(other, intbv):
            val = self._val + other._val*2**(-self._shift)
        else:
            val = int(self._val + other*2**(-self._shift))
        return fixbv(val, self._shift)
            
    __radd__=__add__
    
    def __sub__(self, other):
        if self._isfixbv(other):
            val = float(int(self._val)*2**self._shift - int(other._val)*2**other._shift)
            if self._shift >= other._shift:
                shift = other._shift
            else:
                shift = self._shift
            return fixbv(val, shift)
        elif isinstance(other, intbv):
            val = self._val - other._val*2**(-self._shift)
        else:
            val = self._val - other*2**(-self._shift)
            return fixbv(val, self._shift)

    def __rsub__(self, other):
        if isinstance(other, intbv):
            val = -self._val + other._val*2**(-self._shift)
        else:
            val = -self._val + other*2**(-self._shift)
        return fixbv(val, self._shift)

    def __mul__(self, other):
        if self._isfixbv(other):
            val = self._val * int(other._val)
            shift = self._shift + other._shift
        elif isinstance(other, intbv):
            val = self._val * other._val
            shift = self._shift
        else:
            val = self._val * 2**self._shift * other
            shift = self._shift
        return fixbv(val, shift)
            
    __rmul__=__mul__
    
    def __truediv__(self, other):
        if self._isfixbv(other):
            return float(self._val*2**self._shift) / float(other._val*2**other._shift)
        elif isinstance(other, intbv):
            return float(self._val*2**self._shift) / float(other._val)
        else:
            return float(self._val*2**self._shift) / float(other)
    
    def __rtruediv__(self, other):
        if isinstance(other, intbv):
            return float(other._val) / float(self._val*2**self._shift)
        else:
            return float(other) / float(self._val*2**self._shift)
    
    def __floordiv__(self, other):
        if self._isfixbv(other):
            return int(float(self._val*2**self._shift) // float(other._val*2**other._shift))
        elif isinstance(other, intbv):
            return int(float(self._val*2**self._shift) // float(other._val))
        else:
            return int(float(self._val*2**self._shift) // float(other))

    def __rfloordiv__(self, other):
        if isinstance(other, intbv):
            return int(float(other._val) // float(self._val*2**self._shift))
        else:
            return int(float(other) // float(self._val*2**self._shift))
        
    def __mod__(self, other):
        if self._isfixbv(other):
            return float(self._val*2**self._shift) % float(other._val*2**other._shift)
        if isinstance(other, intbv):
            return float(self._val*2**self._shift) % float(other._val)
        else:
            return float(self._val*2**self._shift) % float(other)

    def __rmod__(self, other):
        if isinstance(other, intbv):
            return float(other._val) % float(self._val*2**self._shift)
        else:
            return float(other) % float(self._val*2**self._shift)

    # divmod
    
    def __pow__(self, other):
        if self._isfixbv(other):
            return float(self._val*2**self._shift)**float(other._val*2**self._shift)
        elif isinstance(other, intbv):
            return float(self._val*2**self._shift)**float(other._val)
        else:
            return float(self._val*2**self._shift)**float(other)

    def __rpow__(self, other):
        if isinstance(other, intbv):
            return float(other._val)**float(self._val*2**self._shift)
        else:
            return other**float(self._val*2**self._shift)

    def __lshift__(self, other):
        if self._isfixbv(other):
            shift = float(other._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift+int(shift))
        elif isinstance(other, intbv):
            shift = float(other._val)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift+int(other._val))
        else:
            shift = float(other)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift+int(other))
            
    def __rlshift__(self, other):
        if isinstance(other, intbv):
            shift = float(self._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return other._val << int(shift)
        else:
            shift = float(self._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return other << int(shift)
            
    def __rshift__(self, other):
        if self._isfixbv(other):
            shift = float(other._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift-int(shift))
        elif isinstance(other, intbv):
            shift = float(other._val)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift-int(other._val))
        else:
            shift = float(other)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return fixbv(self._val, self._shift-int(other))

    def __rrshift__(self, other):
        if isinstance(other, intbv):
            shift = float(self._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return other._val >> int(shift)
        else:
            shift = float(self._val*2**self._shift)
            if (shift % 1.0) != 0:
                raise TypeError("Cannot shift value by an None-integer type")
            return other >> int(shift)

#------------------------------------------------------------------------------            
#                          BITWISE OPERATIONS
#------------------------------------------------------------------------------            
            
    def __and__(self, other):
        if hasattr(other, '_shift') or isinstance(other, intbv):
            return type(self)(self._val & other._val, self._shift)
        else:
            return type(self)(self._val & other, self._shift)
            
    def __rand__(self, other):
        return type(self)(other & self._val, self._shift)

        
    def __or__(self, other):
        if hasattr(other, '_shift') or isinstance(other, intbv):
            return type(self)(self._val | other._val, self._shift)
        else:
            return type(self)(self._val | other, self._shift)
    def __ror__(self, other):
        return type(self)(other | self._val, self._shift)
    
    def __xor__(self, other):
        if hasattr(other, '_shift') or isinstance(other, intbv):
            return type(self)(self._val ^ other._val, self._shift)
        else:
            return type(self)(self._val ^ other, self._shift)

    def __rxor__(self, other):
        return type(self)(other ^ self._val, self._shift)

#------------------------------------------------------------------------------            
#
#------------------------------------------------------------------------------            

    def __iadd__(self, other):
        result = self.__add__(other)
        result._handleBounds()
        return result
        
    def __isub__(self, other):
        result = self.__sub__(other)
        result._handleBounds()
        return result

    def __imul__(self, other):
        result = self.__mul__(other)
        result._handleBounds()
        return result
        
    def __ifloordiv__(self, other):
        result = self.__floordiv__(other)
        result._handleBounds()
        return result
      
    def __idiv__(self, other):
        raise TypeError("fixbv: Augmented classic division not supported")

    def __itruediv__(self, other):
        raise TypeError("fixbv: Augmented true division not supported")
    
    def __imod__(self, other):
        result = self.__mod__(other)
        result._handleBounds()
        return result
        
    def __ipow__(self, other, modulo=None):
        # XXX why 3rd param required?
        # unused but needed in 2.2, not in 2.3 
        result = self.__pow__(other)
        result._handleBounds()
        return result

    def __iand__(self, other):
        result = self.__and__(other)
        result._handleBounds()
        return result


    def __ior__(self, other):
        result = self.__or__(other)
        result._handleBounds()
        return result

    def __ixor__(self, other):
        result = self.__xor__(other)
        result._handleBounds()
        return result

    def __ilshift__(self, other):
        result = self.__lshift__(other)
        result._handleBounds()
        return result

    def __irshift__(self, other):
        result = self.__rshift__(other)
        result._handleBounds()
        return result

    def __neg__(self):
        return -self._val

    def __pos__(self):
        return self._val

    def __abs__(self):
        return abs(self._val)

    def __invert__(self):
        if self._nrbits and self._min >= 0:
            return type(self)(~self._val & (long(1) << self._nrbits)-1)
        else:
            return type(self)(~self._val)
    
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

    def __index__(self):
        return int(self._val)
        
    # comparisons
    def __eq__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift == other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift == other._val
        else:
            return self._val*2**self._shift == other

    def __ne__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift != other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift != other._val
        else:
            return self._val*2**self._shift != other

    def __lt__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift < other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift < other._val
        else:
            return self._val*2**self._shift < other

    def __le__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift <= other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift <= other._val
        else:
            return self._val*2**self._shift <= other

    def __gt__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift > other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift > other._val
        else:
            return self._val*2**self._shift > other

    def __ge__(self, other):
        if self._isfixbv(other):
            return self._val*2**self._shift >= other._val*2**self._shift
        elif isinstance(other, intbv):
            return self._val*2**self._shift >= other._val
        else:
            return self._val*2**self._shift >= other

#---------------------------------------------------------------------------------------------------
#                                       representation
#---------------------------------------------------------------------------------------------------
    #
    # function : __float__
    # brief    : convert the 
    def __float__(self):
        return float(self._val*2.0**self._shift)

    def __int__(self):
        return int(self._val)

    def __str__(self):
        return str(self._val*2.0**self._shift)

    def __repr__(self):
        return "fixbv({} , {}, min={}, max={}, nrbits={})".format(
            repr(self._val), repr(self._shift), repr(self._min), 
            repr(self._max), repr(self._nrbits))


    def signed(self):
      ''' return integer with the signed value of the intbv instance

      The intbv.signed() function will classify the value of the intbv
      instance either as signed or unsigned. If the value is classified
      as signed it will be returned unchanged as integer value. If the
      value is considered unsigned, the bits as specified by _nrbits
      will be considered as 2's complement number and returned. This
      feature will allow to create slices and have the sliced bits be
      considered a 2's complement number.

      The classification is based on the following possible combinations
      of the min and max value.
          
        ----+----+----+----+----+----+----+----
           -3   -2   -1    0    1    2    3
      1                   min  max
      2                        min  max
      3              min       max
      4              min            max
      5         min            max
      6         min       max
      7         min  max
      8   neither min nor max is set
      9   only max is set
      10  only min is set

      From the above cases, # 1 and 2 are considered unsigned and the
      signed() function will convert the value to a signed number.
      Decision about the sign will be done based on the msb. The msb is
      based on the _nrbits value.
      
      So the test will be if min >= 0 and _nrbits > 0. Then the instance
      is considered unsigned and the value is returned as 2's complement
      number.
      '''

      # value is considered unsigned
      if self.min is not None and self.min >= 0 and self._nrbits > 0:

        # get 2's complement value of bits
        msb = self._nrbits-1

        sign = ((self._val >> msb) & 0x1) > 0
        
        # mask off the bits msb-1:lsb, they are always positive
        mask = (1<<msb) - 1
        retVal = self._val & mask
        # if sign bit is set, subtract the value of the sign bit
        if sign:
          retVal -= 1<<msb

      else: # value is returned just as is
        retVal = self._val

      return retVal

#-- end of file '_fixbv.py' ------------------------------------------------------------------------
