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

""" Run the unit tests for enum """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators

import random
from random import randrange
random.seed(1) # random, but deterministic

import unittest
from unittest import TestCase
import sys

from myhdl import enum


class TestEnum(TestCase):

    t_State = enum("SEARCH", "CONFIRM", "SYNC")
    t_Homograph = enum("SEARCH", "CONFIRM", "SYNC")

    def testUniqueLiterals(self):
        try:
            t_State = enum("SEARCH", "CONFIRM", "SEARCH")
        except ValueError:
            pass
        else:
            self.fail()

    def testWrongAttr(self):
        try:
            self.t_State.TYPO
        except AttributeError:
            pass
        else:
            self.fail()

    def testAttrAssign(self):
        self.t_State.SEARCH
        try:
            self.t_State.SEARCH = 4
        except AttributeError:
            pass
        else:
            self.fail()

    def testWrongAttrAssign(self):
        try:
            self.t_State.TYPO = 4
        except AttributeError:
            pass
        else:
            self.fail()

    def testHomograph(self):
        self.assert_(self.t_State is not self.t_Homograph)
        
    def testHomographLiteral(self):
        self.assert_(self.t_State.SEARCH is not self.t_Homograph.SEARCH)


if __name__ == "__main__":
    unittest.main()
