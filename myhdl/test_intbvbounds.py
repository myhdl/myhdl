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

""" Run the intbv unit tests. """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

import unittest
from unittest import TestCase
import random
from random import randrange
random.seed(2) # random, but deterministic
import sys
maxint = sys.maxint
import operator

from intbv import intbv

class TestIntbvBounds(TestCase):
    
    def testConstructor(self):
        self.assertEqual(intbv(40, max=54), 40)
        try:
            intbv(40, max=27)
        except ValueError:
            pass
        else:
            self.fail()
        self.assertEqual(intbv(25, min=16), 25)
        try:
            intbv(25, min=27)
        except ValueError:
            pass
        else:
            self.fail()


    def testSliceAssign(self):
        a = intbv(min=-24, max=34)
        for i in (-24, -2, 13, 33):
            for k in (0, 9, 10):
                a[k:] = i
        for i in (-25, -128, 34, 35, 229):
            for k in (0, 9, 10):
                try:
                    a[k:] = i
                except ValueError:
                    pass
                else:
                    self.fail()
        a = intbv(5)[8:]
        for v in (0, 2**8-1, 100):
            a[:] = v
        for v in (-1, 2**8, -10, 1000):
            try:
                a[:] = v
            except ValueError:
                pass
            else:
                self.fail()
            


    def checkBounds(self, i, j, op):
        a = intbv(i)
        self.assertEqual(a, i) # just to be sure
        try:
            exec("a %s long(j)" % op)
        except (ZeroDivisionError, ValueError):
            return # prune
        if not isinstance(a._val, (int, long)):
            return # prune
        if a > i:
            b = intbv(i, min=i, max=a+1)
            for m in (i+1, a):
                b = intbv(i, min=i, max=m)
                try:
                    exec("b %s long(j)" % op)
                except ValueError:
                    pass
                else:
                    self.fail()
        elif a < i :
            b = intbv(i, min=a, max=i+1)
            exec("b %s long(j)" % op) # should be ok
            for m in (a+1, i):
                b = intbv(i, min=m, max=i+1)
                try:
                    exec("b %s long(j)" % op)
                except ValueError:
                    pass
                else:
                    self.fail()
        else: # a == i
            b = intbv(i, min=i, max=i+1)
            exec("b %s long(j)" % op) # should be ok
            
    def checkOp(self, op):
        for i in (0, 1, -1, 2, -2, 16, -24, 129, -234, 1025, -15660):
            for j in (0, 1, -1, 2, -2, 9, -15, 123, -312, 2340, -23144):
                self.checkBounds(i, j, op)
                
    def testIAdd(self):
        self.checkOp("+=")

    def testISub(self):
        self.checkOp("-=")
        
    def testIMul(self):
        self.checkOp("*=") 
        
    def testIFloorDiv(self):
        self.checkOp("//=")
        
    def testIMod(self):
        self.checkOp("%=")

    def testIPow(self):
        self.checkOp("**=")

    def testIAnd(self):
        self.checkOp("&=")
        
    def testIOr(self):
        self.checkOp("|=")
        
    def testIXor(self):
        self.checkOp("^=")
        
    def testILShift(self):
        self.checkOp("<<=")
        
    def testIRShift(self):
        self.checkOp(">>=")
                    
            
        
        
        
        
       


        


if __name__ == "__main__":
    unittest.main()
       
        
