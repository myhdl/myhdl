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
import copy
import random

import pytest

from myhdl import enum

random.seed(1)  # random, but deterministic


t_State = enum("SEARCH", "CONFIRM", "SYNC")
t_Homograph = enum("SEARCH", "CONFIRM", "SYNC")
t_incomplete = enum("SEARCH", "CONFIRM")

class TestEnum:

    def testUniqueLiterals(self):
        with pytest.raises(ValueError):
            t_State = enum("SEARCH", "CONFIRM", "SEARCH")

    def testWrongAttr(self):
        with pytest.raises(AttributeError):
            t_State.TYPO

    def testAttrAssign(self):
        with pytest.raises(AttributeError):
            t_State.SEARCH = 4

    def testWrongAttrAssign(self):
        with pytest.raises(AttributeError):
            t_State.TYPO = 4

    def testHomograph(self):
        assert t_State is not t_Homograph

    def testHomographLiteral(self):
        assert t_State.SEARCH is not t_Homograph.SEARCH

    def testItemCopy(self):
        e = copy.deepcopy(t_State.SEARCH)
        assert e == t_State.SEARCH
        assert e != t_State.CONFIRM

## Adding test coverage for encoding in enum
 
    def testItemNotDeepCopy(self):
        e = copy.copy(t_State.SEARCH)
        assert e == t_State.SEARCH
        assert e != t_State.CONFIRM

    def testWrongEncoding(self):
        def logic1(encoding):
            t_State = enum("SEARCH", "CONFIRM", "SYNC",encoding=encoding)
            with pytest.raises(ValueError):
            	logic1(encoding)
        
    def testNotStringtype(self):
        with pytest.raises(TypeError):
            t_State = enum("SEARCH", 1, "SYNC")

    def testEnumLength(self):
        l = len(t_State)
        assert l == len(t_State)


