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
_MAXLINE = 4096

class Error(Exception):
    """Cosimulation Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class MultipleCosimError(Error):
    """Only a single cosimulator allowed"""
class DuplicateSigNamesError(Error):
    """Duplicate signal name in myhdl vpi call"""
class SigNotFoundError(Error):
    """Signal not found in Cosimulation arguments"""
class TimeZeroError(Error):
    """myhdl vpi call when not at time 0"""
class NoCommunicationError(Error):
    """No communicating signals"""
class SimulationEndError(Error):
    """Premature simulation end"""


class Cosimulation(object):

    """ Cosimulation class. """

    def __init__(self, exe="", **kwargs):
        
        """ Construct a cosimulation object. """

        global _flag
        if _flag:
            raise MultipleCosimError
        _flag = 1

        # Error = myhdl.Error

        self.rt, self.wt = rt, wt = os.pipe()
        self.rf, self.wf = rf, wf = os.pipe()

        self._fromSignames = fromSignames = []
        self._fromSizes = fromSizes = []
        self._toSignames = toSignames = []
        self._toSizes = toSizes = []

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
                raise Error, str(e)
        else:
            os.close(wt)
            os.close(rf)
            while 1:
                s = os.read(rt, _MAXLINE)
                if not s:
                    raise SimulationEndError
                e = s.split()
                if e[0] == "FROM":
                    for i in range(1, len(e)-1, 2):
                        if e[i] in fromSignames:
                            raise DuplicateSigNamesError, e[i]
                        if not e[i] in kwargs:
                            raise SigNotFoundError, e[i]
                        fromSignames.append(e[i])
                        fromSizes.append(int(e[i+1]))
                    os.write(wf, "OK")
                elif e[0] == "TO":
                    for i in range(1, len(e)-1, 2):
                        if e[i] in toSignames:
                            raise DuplicateSigNamesError, e[i]
                        if not e[i] in kwargs:
                            raise SigNotFoundError, e[i]
                        toSignames.append(e[i])
                        toSizes.append(int(e[i+1]))
                    os.write(wf, "OK")
                else:
                    self.buf = e
                    break
            if long(e[0]) != 0:
                raise TimeZeroError
            if not fromSignames and not toSignames:
                raise NoCommunicationError
            
            
    def __del__(self):
        """ Clear flag when this object destroyed - to suite unittest. """
        global _flag
        _flag = 0

            
     
    

        

        

    

