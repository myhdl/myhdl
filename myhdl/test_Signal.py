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

""" Run the unit tests for Signal """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

import unittest
from unittest import TestCase

from Signal import Signal
from _simulator import _siglist

class SigTest(TestCase):

    def setUp(self):
        self.vals  = (0, 1, 2, 3, 5, [1,2,3], (1,2,3), {1:1, 2:2})
        self.nexts = (1, 0, 0, 4, 5, [4,5,6], (4,5,5), {3:3, 4:4})
        self.sigs = [Signal(i) for i in self.vals]
        self.eventWaiters = [object() for i in range(3)]
        self.posedgeWaiters = [object() for i in range(5)]
        self.negedgeWaiters = [object() for i in range(7)]

    def testPublicInterface(self):
        """ public interface of a sig: val, next, posedge, negedge"""
        s1 = Signal(1)
        expected = ['next', 'val', 'posedge', 'negedge']
        iface = [attr for attr in dir(s1) if attr[0] != '_']
        expected.sort()
        iface.sort()
        self.assertEqual(iface, expected)
        
    def testValAttrReadOnly(self):
        """ val attribute should not be writable"""
        s1 = Signal(1)
        try:
            self.s1.val = 1
        except AttributeError:
            pass
        else:
            self.fail()

    def testPosedgeAttrReadOnly(self):
        """ val attribute should not be writable"""
        s1 = Signal(1)
        try:
            self.s1.posedge = 1
        except AttributeError:
            pass
        else:
            self.fail()
            
    def testNegedgeAttrReadOnly(self):
        """ val attribute should not be writable"""
        s1 = Signal(1)
        try:
            self.s1.negedge = 1
        except AttributeError:
            pass
        else:
            self.fail()

    def testInitParamRequired(self):
        """ a Signal constructor has a required parameter """
        self.assertRaises(TypeError, Signal)

    def testInitialization(self):
        """ initial val and next should be equal but not identical """
        for s in self.sigs:
            self.assertEqual(s.val, s.next)

    def testUpdate(self):
        """ _update() should assign next into val """
        for s, n in zip(self.sigs, self.nexts):
            s.next = n
            s._update()
            self.assert_(s.val == n)

    def testAfterUpdate(self):
        """ updated val and next should be equal but not identical """
        for s, n in zip(self.sigs, self.nexts):
            s.next = n
            s._update()
            self.assertEqual(s.val, s.next)
            
    def testModify(self):
        """ Modifying mutable next should be on a copy """
        for s in self.sigs:
            mutable = 0
            try:
                hash(s.val)
            except TypeError:
                mutable = 1
            if not mutable:
                continue
            if type(s.val) is list:
                s.next.append(1)
            elif type(s.val) is dict:
                s.next[3] = 5
            else:
                s.next # plain read access
            self.assert_(s.val is not s.next, `s.val`)

    def testUpdatePosedge(self):
        """ update on posedge should return event and posedge waiters """
        s1 = Signal(1)
        s1.next = 0
        s1._update()
        s1.next = 1
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters + self.posedgeWaiters
        waiters.sort()
        expected.sort()
        self.assertEqual(waiters, expected)
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, [])
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
            
    def testUpdateNegedge(self):
        """ update on negedge should return event and negedge waiters """
        s1 = Signal(1)
        s1.next = 1
        s1._update()
        s1.next = 0
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters + self.negedgeWaiters
        waiters.sort()
        expected.sort()
        self.assertEqual(waiters, expected)
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, [])

    def testUpdateEvent(self):
        """ update on non-edge event should return event waiters """
        s1 = Signal(1)
        s1.next = 4
        s1._update()
        s1.next = 5
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        expected = self.eventWaiters
        waiters.sort()
        expected.sort()
        self.assertEqual(waiters, expected)
        self.assertEqual(s1._eventWaiters, [])
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
        
    def testUpdateNoEvent(self):
        """ update without value change should not return event waiters """
        s1 = Signal(1)
        s1.next = 4
        s1._update()
        s1.next = 4
        s1._eventWaiters = self.eventWaiters[:]
        s1._posedgeWaiters = self.posedgeWaiters[:]
        s1._negedgeWaiters = self.negedgeWaiters[:]
        waiters = s1._update()
        self.assertEqual(waiters, [])
        self.assertEqual(s1._eventWaiters, self.eventWaiters)
        self.assertEqual(s1._posedgeWaiters, self.posedgeWaiters)
        self.assertEqual(s1._negedgeWaiters, self.negedgeWaiters)
    
    def testNextAccess(self):
        """ each next attribute access puts a sig in a global siglist """
        del _siglist[:]
        s = [None] * 4
        for i in range(len(s)):
            s[i] = Signal(i)
        s[1].next # read access
        s[2].next = 1
        s[2].next
        s[3].next = 0
        s[3].next = 1
        s[3].next = 3
        for i in range(len(s)):
            self.assertEqual(_siglist.count(s[i]), i)
    

if __name__ == "__main__":
    unittest.main()
