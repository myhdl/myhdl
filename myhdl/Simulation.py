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

""" Module that provides the Simulation class """

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

from __future__ import generators
import sys
import os
from warnings import warn
from types import GeneratorType

import _simulator
from _simulator import _siglist, _futureEvents
from Signal import Signal, _WaiterList
from delay import delay
from Cosimulation import Cosimulation
from join import join
from _Waiter import _Waiter
from util import StopSimulation, SuspendSimulation
import simrun
import simrunc

schedule = _futureEvents.append

class Error(Exception):
    """Simulation Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class MultipleCosimError(Error):
    """Only a single cosimulator argument allowed"""

            
class Simulation(object):

    """ Simulation class.

    Methods:
    run -- run a simulation for some duration

    """

    def __init__(self, *args):
        """ Construct a simulation object.

        *args -- list of arguments. Each argument is a generator or
                 a nested sequence of generators.

        """
        _simulator._time = 0
        self._waiters, self._cosim = _flatten(*args)
        if not self._cosim and _simulator._cosim:
            warn("Cosimulation not registered as Simulation argument")
        del _futureEvents[:]
        del _siglist[:]
        
    def _finalize(self):
        cosim = self._cosim
        if cosim:
            _simulator._cosim = 0
            os.close(cosim._rt)
            os.close(cosim._wf)
            os.waitpid(cosim._child_pid, 0)
        
    def run(self, duration=0, quiet=0):
        simrunc.run(sim=self, duration=duration, quiet=quiet)
        
    runpy = simrun.run


def printExcInfo():
    kind, value, traceback = sys.exc_info()
    msg = str(kind)
    msg = msg[msg.rindex('.')+1:]
    if str(value):
        msg += ": %s" % value
        print msg
        
     
def _flatten(*args):
    waiters = []
    cosim = None
    for arg in args:
        if type(arg) is GeneratorType:
            waiters.append(_Waiter(arg))
        elif type(arg) is Cosimulation:
            if cosim:
                raise MultipleCosimError
            cosim = arg
            waiters.append(_Waiter(cosim._waiter()))
        else:
            for item in arg:
                w, c = _flatten(item)
                if cosim and c:
                    raise MultipleCosimError
                cosim = c
                waiters.extend(w)
    return waiters, cosim

