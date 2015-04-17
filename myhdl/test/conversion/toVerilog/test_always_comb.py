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

""" Run the unit tests for always_comb """
from __future__ import absolute_import


import random
from random import randrange
# random.seed(3) # random, but deterministic
import os
from os import path

import unittest
from unittest import TestCase

from myhdl import *

from util import setupCosimulation

QUIET = 1

def design1(a, b, c, d, p, q, r):
    def logic():
        p.next = a | b
    return always_comb(logic)

def design2(a, b, c, d, p, q, r):
    def logic():
        p.next = a | b
        q.next = c & d
        r.next = a ^ c
    return always_comb(logic)

def design3(a, b, c, d, p, q, r):
    def logic():
        if a:
            p.next = c | b
            q.next = c & d
            r.next = d ^ c
    return always_comb(logic)

def design4(a, b, c, d, p, q, r):
    def logic():
        p.next = a | b
        q.next = c & d
        r.next = a ^ c
        q.next = c | d
    return always_comb(logic)

def design5(a, b, c, d, p, q, r):
    def logic():
        p.next = a | b
        q.next = c & d
        r.next = a ^ c
        q.next[0] = c | d
        
    return always_comb(logic)


def design_v(name, a, b, c, d, p, q, r):
    return setupCosimulation(**locals())
    

class AlwaysCombSimulationTest(TestCase):

    def bench(self, design):

        clk = Signal(0)
        a = Signal(bool(0))
        b = Signal(bool(0))
        c = Signal(bool(0))
        d = Signal(bool(0))
        k = Signal(intbv(0)[8:])
        p = Signal(bool(0))
        q = Signal(intbv(0)[8:])
        r = Signal(bool(0))
        p_v = Signal(bool(0))
        q_v = Signal(intbv(0)[8:])
        r_v = Signal(bool(0))
        vectors = [intbv(j) for i in range(50) for j in range(16)]
        random.shuffle(vectors)

        design_inst = toVerilog(design, a, b, c, d, p, q, r)
        design_v_inst = design_v(design.__name__, a, b, c, d, p_v, q_v, r_v)

        def clkGen():
            while 1:
                yield delay(10)
                clk.next ^= 1

        def stimulus():
            for v in vectors:
                a.next = v[0]
                b.next = v[1]
                c.next = v[2]
                d.next = v[3]
                k.next = v
                yield clk.posedge
                yield clk.negedge
                # print p, q, r
                self.assertEqual(p, p_v)
                self.assertEqual(q, q_v)
                self.assertEqual(r, r_v)
                
            raise StopSimulation("always_comb simulation test")

        return design_inst, design_v_inst, clkGen(), stimulus()
        

    def test1(self):
        Simulation(self.bench(design1)).run(quiet=QUIET)
        
    def test2(self):
        Simulation(self.bench(design2)).run(quiet=QUIET)
        
    def test3(self):
        Simulation(self.bench(design3)).run(quiet=QUIET)
    
    def test4(self):
        Simulation(self.bench(design4)).run(quiet=QUIET)
        
    def test5(self):
        Simulation(self.bench(design5)).run(quiet=QUIET)
        
        

if __name__ == "__main__":
    unittest.main()
