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

""" Module that provides the Cosimulation class """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators
import sys
import os
import exceptions

from Signal import Signal
import myhdl

_flag = 0
MAXLINE = 4096

class Cosimulation(object):

    """ Cosimulation class. """

    def __init__(self, exe="", **kwargs):
        
        """ Construct a cosimulation object. """

        global _flag
        if _flag:
            raise myhdl.Error, "Cosimulation: Only a single cosimulator allowed"
        _flag = 1

        self.rt, self.wt = rt, wt = os.pipe()
        self.rf, self.wf = rf, wf = os.pipe()

        self._fromSigs = []
        self._fromSizes = []
        self._toSigs = []
        self._toSizes = []

        child_pid = os.fork()

        if child_pid == 0:
            os.close(rt)
            os.close(wf)
            os.environ['MYHDL_TO_PIPE'] = str(wt)
            os.environ['MYHDL_FROM_PIPE'] = str(rf)
            arglist = exe.split()
            try:
                os.execvp(arglist[0], arglist)
            except OSError, e:
                raise myhdl.Error, "Cosimulation: " + str(e)
        else:
            os.close(wt)
            os.close(rf)
            while 1:
                s = os.read(rt, MAXLINE)
                if not s:
                    raise myhdl.Error, "Cosimulation down"
                e = s.split()
                if e[0] == "FROM":
                    self._fromSigs = [e[i] for i in range(1, len(e), 2)]
                    self._fromSizes = [int(e[i]) for i in range(2, len(e), 2)]
                    os.write(wf, "OK")
                elif e[0] == "TO":
                    self._toSigs = [e[i] for i in range(1, len(e), 2)]
                    self._toSizes = [int(e[i]) for i in range(2, len(e), 2)]
                    os.write(wf, "OK")
                else:
                    self.buf = e
                    break
            if long(e[0]) != 0:
                raise myhdl.Error, "Cosimulation: myhdl call when not at time 0"
            if not self._fromSigs and not self._toSigs:
                raise myhdl.Error, "Cosimulation: no communicating signals"
            
            

    def __del__(self):
        """ Clear flag when this object destroyed - to suite unittest. """
        global _flag
        _flag = 0

            
     
    

        

        

    

