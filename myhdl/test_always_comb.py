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

""" Run the unit tests for always_comb """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators
import random
from random import randrange
random.seed(1) # random, but deterministic

import unittest
from unittest import TestCase

from always_comb import always_comb
from always_comb import ScopeError, ArgumentError, NrOfArgsError

def g():
    pass

class AlwaysCombTest(TestCase):

    def testArgIsFunction(self):
        h = 5
        try:
            always_comb(h)
        except ArgumentError:
            pass
        else:
            self.fail()

    
    def testArgIsNormalFunction(self):
        def h():
            yield None
        try:
            always_comb(h)
        except ArgumentError:
            pass
        else:
            self.fail()

    def testArgHasNoArgs(self):
        def h(n):
            return n
        try:
            always_comb(h)
        except NrOfArgsError:
            pass
        else:
            self.fail()
        
        

    def testScope(self):
        try:
            always_comb(g)
        except ScopeError:
            pass
        else:
            self.fail()


if __name__ == "__main__":
    unittest.main()
