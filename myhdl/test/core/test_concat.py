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

""" Run the concatunit tests. """
from __future__ import absolute_import


import unittest
from unittest import TestCase
import random
from random import randrange
from functools import reduce
random.seed(2) # random, but deterministic
import operator

from myhdl._intbv import intbv
from myhdl._Signal import Signal
from myhdl._concat import concat
from myhdl._compat import long



class TestConcat(TestCase):

    bases = ("0", "1", "10101", "01010", "110", "011", "1001000100001011111000")
    extslist = [ ["0"], ["1"], ["00"], ["11"], ["000"], ["111"], ["1010101010"],
                 ["0", "1"], ["1", "0"], ["1", "01", "10"], ["11111", "001001"],
                 ["110001111101110", "10101110111001001", "111001101000101010"],
                 ["1100", "1", "01001", "0", "10", "01", "0", "0", "11", "1"  ]
               ]

    def ConcatToSizedBase(self, bases, extslist):
        for base, basestr in zip(bases, self.bases):
            for exts, extstr in zip(extslist, self.extslist):
                bv = concat(base, *exts)
                refstr = basestr + reduce(operator.add, extstr)
                reflen = len(refstr)
                ref = long(refstr, 2)
                self.assertEqual(bv, ref)
                self.assertEqual(len(bv), reflen)

    def ConcatToUnsizedBase(self, bases, extslist):
        for base, basestr in zip(bases, self.bases):
            for exts, extstr in zip(extslist, self.extslist):
                bv = concat(base, *exts)
                refstr = basestr + reduce(operator.add, extstr)
                ref = long(refstr, 2)
                self.assertEqual(bv, ref)
                self.assertEqual(len(bv), 0)


    def testConcatStringsToString(self):
        bases = self.bases
        extslist = self.extslist
        self.ConcatToSizedBase(bases, extslist)

    def testConcatStringsToInt(self):
        bases = [long(base, 2) for base in self.bases]
        extslist = self.extslist
        self.ConcatToUnsizedBase(bases, extslist)
        
    def testConcatStringsToSignalInt(self):
        bases = [Signal(long(base, 2)) for base in self.bases]
        extslist = self.extslist
        self.ConcatToUnsizedBase(bases, extslist)
                
    def testConcatStringsToIntbv(self):
        bases = [intbv(base) for base in self.bases]
        extslist = self.extslist
        self.ConcatToSizedBase(bases, extslist)

    def testConcatStringsToSignalIntbv(self):
        bases = [Signal(intbv(base)) for base in self.bases]
        extslist = self.extslist
        self.ConcatToSizedBase(bases, extslist)

    def testConcatStringsToBool(self):
        if type(bool) is not type:
            return
        bases = []
        for base in self.bases:
            if len(base) == 1:
                bases.append(bool(int(base)))
            else:
                bases.append(intbv(base))
        extslist = self.extslist
        self.ConcatToSizedBase(bases, extslist)
        
    def testConcatStringsToSignalBool(self):
        if type(bool) is not type:
            return
        bases = []
        for base in self.bases:
            if len(base) == 1:
                bases.append(Signal(bool(int(base))))
            else:
                bases.append(intbv(base))
        extslist = self.extslist
        self.ConcatToSizedBase(bases, extslist)
        
        
    def testConcatIntbvsToIntbv(self):
        bases = [intbv(base) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([intbv(ext) for ext in exts])
        self.ConcatToSizedBase(bases, extslist)
        
    def testConcatSignalIntbvsToIntbv(self):
        bases = [intbv(base) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([Signal(intbv(ext)) for ext in exts])
        self.ConcatToSizedBase(bases, extslist)

    def testConcatIntbvsToSignalIntbv(self):
        bases = [Signal(intbv(base)) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([intbv(ext) for ext in exts])
        self.ConcatToSizedBase(bases, extslist)

    def testConcatSignalIntbvsToSignalIntbv(self):
        bases = [Signal(intbv(base)) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([Signal(intbv(ext)) for ext in exts])
        self.ConcatToSizedBase(bases, extslist)

    
    def testConcatIntbvsToInt(self):
        bases = [long(base, 2) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([intbv(ext) for ext in exts])
        self.ConcatToUnsizedBase(bases, extslist)
        
    def testConcatSignalIntbvsToInt(self):
        bases = [long(base, 2) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([Signal(intbv(ext)) for ext in exts])
        self.ConcatToUnsizedBase(bases, extslist)

    def testConcatIntbvsToSignalInt(self):
        bases = [Signal(long(base, 2)) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([intbv(ext) for ext in exts])
        self.ConcatToUnsizedBase(bases, extslist)

    def testConcatSignalIntbvsToSignalInt(self):
        bases = [Signal(long(base, 2)) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            extslist.append([Signal(intbv(ext)) for ext in exts])
        self.ConcatToUnsizedBase(bases, extslist)
        

    def testConcatIntbvsBoolsToIntbv(self):
        if type(bool) is not type:
            return
        bases = [intbv(base) for base in self.bases]
        extslist = []
        for exts in self.extslist:
            newexts = []
            for ext in exts:
                if len(ext) == 1:
                    newexts.append(bool(int(ext)))
                else:
                    newexts.append(intbv(ext))
            extslist.append(newexts)
        self.ConcatToSizedBase(bases, extslist)
    

    def testConcatMixToSizedBase(self):
        bases = []
        for base in self.bases:
            seq = (base, intbv(base), Signal(intbv(base)))
            bases.append(random.choice(seq))
        extslist = []
        for exts in self.extslist:
            newexts = []
            for ext in exts:
                seq = (ext, intbv(ext), Signal(intbv(ext)))
                newexts.append(random.choice(seq))
            extslist.append(newexts)
        self.ConcatToSizedBase(bases, extslist)

    def testConcatMixToUnsizedBase(self):
        bases = []
        for base in self.bases:
            seq = (long(base, 2), Signal(long(base, 2)))
            bases.append(random.choice(seq))
        extslist = []
        for exts in self.extslist:
            newexts = []
            for ext in exts:
                seq = (ext, intbv(ext), Signal(intbv(ext)))
                newexts.append(random.choice(seq))
            extslist.append(newexts)
        self.ConcatToUnsizedBase(bases, extslist)
        

    def testConcatMixBoolToSizedBase(self):
        if type(bool) is not type:
            return
        bases = []
        for base in self.bases:
            seq = (base, intbv(base), Signal(intbv(base)))
            bases.append(random.choice(seq))
        extslist = []
        for exts in self.extslist:
            newexts = []
            for ext in exts:
                if len(ext) == 1:
                    seq = (ext, bool(int(ext)), Signal(bool(int(ext))))
                else:
                    seq = (ext, intbv(ext), Signal(intbv(ext)))
                newexts.append(random.choice(seq))
            extslist.append(newexts)
        self.ConcatToSizedBase(bases, extslist)
               

    def testWrongType(self):
        a = intbv(4)
        self.assertRaises(TypeError, concat, a, 5)
            
    def testUnsizedConcat(self):
        a = intbv(4)
        b = intbv(5)
        self.assertRaises(TypeError, concat, a, b)

if __name__ == "__main__":
    unittest.main()
       
        
