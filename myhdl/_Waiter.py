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

""" Module that provides the _Waiter class """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators

from myhdl._join import join
from myhdl._simulator import _siglist, _futureEvents;


class _Waiter(object):
    
    def __init__(self, generator, caller=None, semaphore=None):
        self.generator = generator
        self.hasRun = 0
        self.caller = caller
        self.semaphore = None
        
    def next(self):
        self.hasRun = 1
        clone = _Waiter(self.generator, self.caller, self.semaphore)
        clause = self.generator.next()
        if type(clause) is tuple:
            return clause, clone
        elif type(clause) is join:
            n = len(clause._args)
            clone.semaphore = _Semaphore(n)
            return clause._args, clone
        else:
            return (clause,), clone
    
    def hasGreenLight(self):
        if self.semaphore:
            self.semaphore.val -= 1
            if self.semaphore.val != 0:
                return 0
        return 1
    
           
class _Semaphore(object):
    def __init__(self, val=1):
        self.val = val
        
       
class _WaiterList(list):

    def purge(self):
        if self:
            self[:] = [w for w in self if not w.hasRun]
