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

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Run the unit tests for enum """
from __future__ import absolute_import


import random
from random import randrange
random.seed(1) # random, but deterministic

import sys
import copy

import unittest
from unittest import TestCase

from myhdl import enum


t_State = enum("SEARCH", "CONFIRM", "SYNC")
t_Homograph = enum("SEARCH", "CONFIRM", "SYNC")


class TestEnum(TestCase):

    def testUniqueLiterals(self):
        try:
            t_State = enum("SEARCH", "CONFIRM", "SEARCH")
        except ValueError:
            pass
        else:
            self.fail()

    def testWrongAttr(self):
        try:
            t_State.TYPO
        except AttributeError:
            pass
        else:
            self.fail()

    def testAttrAssign(self):
        try:
            t_State.SEARCH = 4
        except AttributeError:
            pass
        else:
            self.fail()

    def testWrongAttrAssign(self):
        try:
            t_State.TYPO = 4
        except AttributeError:
            pass
        else:
            self.fail()

    def testHomograph(self):
        self.assertTrue(t_State is not t_Homograph)
        
    def testHomographLiteral(self):
        self.assertTrue(t_State.SEARCH is not t_Homograph.SEARCH)

    def testItemCopy(self):
        e = copy.deepcopy(t_State.SEARCH)
        self.assertTrue(e == t_State.SEARCH)
        self.assertTrue(e != t_State.CONFIRM)


if __name__ == "__main__":
    unittest.main()
