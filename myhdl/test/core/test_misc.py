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

""" Run the unit tests for Signal """
from __future__ import absolute_import


import random
from random import randrange
random.seed(1) # random, but deterministic
from types import GeneratorType

import unittest
from unittest import TestCase

from myhdl import instance, instances

def A(n):
    @instance
    def logic():
        yield None
    return logic

def B(n):
    @instance
    def logic():
        yield None
    return logic

def C(n):
    A_1 = A(1)
    A_2 = A(2)
    B_1 = B(1)
    return A_1, A_2, B_1

g = 3

class InstancesTest(TestCase):

    def testInstances(self):

        @instance
        def D_1():
            yield None
        d = 1

        A_1 = A(1)
        a = [1, 2]
        B_1 = B(1)
        b = "string"
        C_1 = C(1)
        c = {}

        i = instances()
        # can't just construct an expected list;
        # that would become part of the instances also!
        self.assertEqual(len(i), 4)
        for e in (D_1, A_1, B_1, C_1):
            self.assertTrue(e in i)


if __name__ == "__main__":
    unittest.main()
