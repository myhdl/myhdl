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

""" Run the unit tests for inferWaiter """
from __future__ import absolute_import


import random
from random import randrange
random.seed(1) # random, but deterministic

import myhdl
from myhdl import *
from myhdl._Waiter import _SignalWaiter,_SignalTupleWaiter, _DelayWaiter, \
                          _EdgeWaiter, _EdgeTupleWaiter, _Waiter
from test_inferWaiter import *



QUIET=1


N=10

def bench(genFunc, waiterType):

    a, b, c, d, r, s = [Signal(intbv()) for i in range(6)]

    s = [Signal(intbv()) for i in range(N)]
    gen_inst_s = []

    for i in range(N):
        gen_inst_s.append(waiterType(genFunc(a, b, c, d, s[i])))

    def stimulus():
        for i in range(5000):
            yield delay(randrange(1, 10))
            if randrange(2):
                a.next = randrange(32)
            if randrange(2):
                b.next = randrange(32)
            c.next = randrange(2)
            d.next = randrange(2)
        raise StopSimulation()

    return gen_inst_s, _Waiter(stimulus())


gen = SignalGen2

waiter = _Waiter

sim = Simulation(bench(gen, waiter))
sim.run()


