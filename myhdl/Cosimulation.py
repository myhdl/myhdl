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
import _simulator
from myhdl import intbv

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
        
        if _simulator._cosim:
            raise MultipleCosimError
        _simulator._cosim = 1
        
        self._rt, self._wt = rt, wt = os.pipe()
        self._rf, self._wf = rf, wf = os.pipe()

        self._fromSignames = fromSignames = []
        self._fromSizes = fromSizes = []
        self._fromSigs = fromSigs = []
        self._toSignames = toSignames = []
        self._toSizes = toSizes = []
        self._toSigs = toSigs = []

        self._hasChange = 0

        child_pid = self._child_pid = os.fork()

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
                    if long(e[1]) != 0:
                        raise TimeZeroError, "$from_myhdl"
                    for i in range(2, len(e)-1, 2):
                        n = e[i]
                        if n in fromSignames:
                            raise DuplicateSigNamesError, n
                        if not n in kwargs:
                            raise SigNotFoundError, n
                        fromSignames.append(n)
                        fromSigs.append(kwargs[n])
                        fromSizes.append(int(e[i+1]))
                    os.write(wf, "OK")
                elif e[0] == "TO":
                    if long(e[1]) != 0:
                        raise TimeZeroError, "$to_myhdl"
                    for i in range(2, len(e)-1, 2):
                        n = e[i]
                        if n in toSignames:
                            raise DuplicateSigNamesError, n
                        if not n in kwargs:
                            raise SigNotFoundError, n
                        toSignames.append(n)
                        toSigs.append(kwargs[n])
                        toSizes.append(int(e[i+1]))
                    os.write(wf, "OK")
                elif e[0] == "START":
                    if not toSignames:
                        raise NoCommunicationError
                    os.write(wf, "OK")
                    break
                else:
                    raise Error, "Unexpected cosim input"
            # os.waitpid(child_pid, 0)

    def _get(self):
        s = os.read(self._rt, _MAXLINE)
        if not s:
            raise SimulationEndError
        e = s.split()
        vals = e[1:]
        for s, v in zip(self._toSigs, vals):
            try:
                next = long(v, 16)
            except ValueError:
                next = intbv(None)
            if s.val != next:
                s.next = next

    def _put(self, time):
        t = hex(time)[2:]
        if t[-1] == 'L':
            t = t[:-1] # strip trailing L
        t = (9 - len(t)) * '0' + t # zero-extend to more than 32 bits
        buf = t[:-8] + " " + t[-8:] + " " # high and low time
        for s in self._fromSigs:
            buf += hex(s)[2:]
            buf += " "
        self._hasChange = 0
        os.write(self._wf, buf)

    def _waiter(self):
        sigs = tuple(self._fromSigs)
        while 1:
            yield sigs
            self._hasChange = 1
            
    def __del__(self):
        """ Clear flag when this object destroyed - to suite unittest. """
        _simulator._cosim = 0
