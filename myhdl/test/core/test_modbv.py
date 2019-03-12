#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2011 Jan Decaluwe
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

""" Run the modbv unit tests. """
import sys
import random
import pytest


from random import randrange

from myhdl._intbv import intbv
from myhdl._modbv import modbv

random.seed(3)
maxint=sys.maxsize


class TestModbvWrap:

    def testWrap(self):
        x = modbv(0, min=-8, max=8)
        x[:] = x + 1
        assert 1 == x
        x[:] = x + 2
        assert 3 == x
        x[:] = x + 5
        assert -8 == x
        x[:] = x + 1
        assert -7 == x
        x[:] = x - 5
        assert 4 == x
        x[:] = x - 4
        assert 0 == x
        x[:] += 15
        x[:] = x - 1
        assert -2 == x

    def testInit(self):
        with pytest.raises(ValueError):
            intbv(15, min=-8, max=8)

        x = modbv(15, min=-8, max=8)
        assert -1 == x

        # Arbitrary boundraries support (no exception)
        modbv(5, min=-3, max=8)

    def testNoWrap(self):
        # Validate the base class fails for the wraps
        x = intbv(0, min=-8, max=8)
        with pytest.raises(ValueError):
            x[:] += 15

        x = intbv(0, min=-8, max=8)
        with pytest.raises(ValueError):
            x[:] += 15


class TestModBvSlice:

    def BuildTestSeqs(self):
        imin,jmin=0,0
        imax,jmax=5000,5000
        seqi,seqj=[],[]
        #small bits
        for n in range(10):
            seqi.append(randrange(imin, imax))
            seqi.append(randrange(jmin, jmax))
        #large bits
        for n in range(10):
            seqi.append(randrange(imin,maxint))
            seqj.append(randrange(jmin,maxint))
        self.seqi=seqi
        self.seqj=seqj

    def testGetItem(self):
        self.BuildTestSeqs()        
        #Testing for the __getItem__ function
        for i in self.seqi:
            ti=modbv(i)
            cti=modbv(~i)
            for n in range(len(bin(i))):
                chk=((i >> n) & 1)
                res=ti[n]
                resv=cti[n]
                assert type(res) == bool
                assert type(resv) == bool 
                assert res == chk
                assert resv == chk^1
                

    def testGetSlice(self):
        self.BuildTestSeqs()
        #Testing for slice ranged, both closed
        for i in self.seqi:
            ti=modbv(i)
            cti=modbv(~i)
            leni=len(bin(i))
            for n in (range(leni)):
                s=randrange(-leni,leni)
                f=randrange(-leni,leni)
                try:
                    val=ti[f:s]
                except ValueError:
                    assert (f<=s) | (s<=0)
                else:
                    chkt = (i >> s) & (2**(f-s) -1)
                    assert val == chkt
                    assert (val.max,val.min) == (2**(f-s),0)

    def testGetSliceOpen(self):
        self.BuildTestSeqs()
        #Testing for slice ranged, one of them open
        for i in self.seqi:
            ti=modbv(i)
            cti=modbv(~i)
            leni=len(bin(i))  
            assert ti+cti == -1
            for n in (range(leni)):
                s=randrange(leni)
                f=randrange(1,leni)
                chkf = (i) & (2**(f) -1)
                chks = (i >> s)
                vals,cvals = ti[:s],cti[:s]
                valf,cvalf = ti[f:],cti[f:]
                assert vals+cvals == -1
                
                #assert valf+cvalf == -1   ---test fails- why???
                assert vals == modbv(chks)
                assert valf == modbv(chkf)

    def testSetSlice(self):
        self.BuildTestSeqs()
        self.seqi.extend(self.seqj)
        #Test the bit slice setting wrap around behaviour
        for i in range(1,len(self.seqi)):
            lenp=len(bin(self.seqi[i-1]))
            ti = modbv(self.seqi[i-1])[lenp:]
            maxp = 2**lenp
            vali = self.seqi[i]
            s=randrange(lenp-1)
            f=randrange(s,lenp)
            valp = self.seqi[i-1]
            maxval = (1 << (f-s))-1
            try:
                ti[f:s] = vali
            except ValueError:
                assert maxval < vali
            else:
                bitmask = (((2**f - 1) >> s) << s )
                valp = valp - (valp & bitmask)
                valp = (valp + ((vali << s) % maxp)) % maxp
                assert valp == ti

        
                 
                
                
                
                
        


	
