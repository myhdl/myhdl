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

""" Run the unit tests for instance """
from __future__ import absolute_import


import random
from random import randrange
# random.seed(3) # random, but deterministic

import unittest
from unittest import TestCase
import inspect

from myhdl import Signal, Simulation, instances, InstanceError, \
                  intbv, delay, StopSimulation, now

from myhdl._instance import instance, _error



QUIET=1

def g():
    pass

x = Signal(0)

class InstanceCompilationTest(TestCase):
    

    def testArgIsFunction(self):
        h = 5
        try:
            instance(h)
        except InstanceError as e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()
    
    def testArgIsGeneratorFunction(self):
        try:
            @instance
            def h():
                return None
        except InstanceError as e:
            self.assertEqual(e.kind, _error.ArgType)
        else:
            self.fail()

    def testArgHasNoArgs(self):
        try:
            @instance
            def h(n):
                yield n
        except InstanceError as e:
            self.assertEqual(e.kind, _error.NrOfArgs)
        else:
            self.fail()


if __name__ == "__main__":
    unittest.main()
