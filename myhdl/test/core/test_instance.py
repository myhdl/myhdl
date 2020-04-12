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
from myhdl import (InstanceError, Signal, Simulation, StopSimulation, delay,
                   instances, intbv, now)
from myhdl._instance import _error, instance
from helpers import raises_kind

# random.seed(3) # random, but deterministic


QUIET=1


def g():
    pass

x = Signal(0)


class TestInstanceCompilation:

    def testArgIsFunction(self):
        h = 5
        with raises_kind(InstanceError, _error.ArgType):
            instance(h)

    def testArgIsGeneratorFunction(self):
        with raises_kind(InstanceError, _error.ArgType):
            @instance
            def h():
                return None

    def testArgHasNoArgs(self):
        with raises_kind(InstanceError, _error.NrOfArgs):
            @instance
            def h(n):
                yield n
