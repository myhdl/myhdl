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


from myhdl._join import join
from myhdl._simulator import _siglist, _futureEvents


class _Waiter(object):

    __slots__ = ('caller', 'generator', 'hasRun', 'nrTriggers', 'semaphore')
    
    def __init__(self, generator, caller=None):
        self.caller = caller
        self.generator = generator
        self.hasRun = 0
        self.nrTriggers = 1
        self.semaphore = 0
        
    def next(self):
        if self.nrTriggers == 1:
            clone = self
        else:
            self.hasRun = 1
            clone = _Waiter(self.generator, self.caller)
        clause = self.generator.next()
        if isinstance(clause, _WaiterList):
            return (clause,), clone
        elif isinstance(clause, (tuple, list)):
            clone.nrTriggers = len(clause)
            if clause:
                return clause, clone
            else:
                return (None,), clone
        elif isinstance(clause, join):
            clone.semaphore = len(clause._args)-1
            return clause._args, clone
        else:
            return (clause,), clone
    
    def hasGreenLight(self):
        if self.semaphore:
            self.semaphore -= 1
            return 0
        else:
            return 1
    
       
class _WaiterList(list):

    def purge(self):
        if self:
            self[:] = [w for w in self if not w.hasRun]
