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

""" Run the unit tests for bin """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators

import random
from random import randrange
random.seed(1) # random, but deterministic
import sys
import os
path = os.path

import unittest
from unittest import TestCase

from myhdl import delay, Signal
from trace_sigs import trace_sigs, TopLevelNameError, ArgTypeError, \
                       NoInstancesError

def gen(clk):
    while 1:
        yield delay(10)
        clk.next = not clk

def fun():
    clk = Signal(bool(0))
    inst = gen(clk)
    return inst

def dummy():
    clk = Signal(bool(0))
    inst = gen(clk)
    return 1

def top():
    inst = trace_sigs(fun)
    return inst


class TestTraceSigs(TestCase):

    def testTopName(self):
        p = "dut.vcd"
        if path.exists(p):
            os.remove(p)
        dut = trace_sigs(fun)
        try:
            trace_sigs(fun)
        except TopLevelNameError:
            pass
        else:
            self.fail()

    def testArgType1(self):
        p = "dut.vcd"
        if path.exists(p):
            os.remove(p)
        try:
            dut = trace_sigs([1, 2])
        except ArgTypeError:
            pass
        else:
            self.fail()
            
    def testArgType2(self):
        p = "dut.vcd"
        if path.exists(p):
            os.remove(p)
        try:
            dut = trace_sigs(gen, Signal(0))
        except ArgTypeError:
            pass
        else:
            self.fail()

    def testReturnVal(self):
        p = "dut.vcd"
        if path.exists(p):
            os.remove(p)
        try:
            dut = trace_sigs(dummy)
        except NoInstancesError:
            pass
        else:
            self.fail()

    def testHierarchicalTrace1(self):
        p = "inst.vcd"
        if path.exists(p):
            os.remove(p)
        top()
        self.assert_(path.exists(p))
        
    def testHierarchicalTrace2(self):
        pdut = "dut.vcd"
        psub = "inst.vcd"
        for p in (pdut, psub):
            if path.exists(p):
                os.remove(p)
        dut = trace_sigs(top)
        self.assert_(path.exists(pdut))
        self.assert_(not path.exists(psub))

    
        
        
       
       

if __name__ == "__main__":
    unittest.main()
