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
try:
    import simrunc
except:
    pass


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
            
        
    def runc(self, duration=0, quiet=0):
        simrunc.run(sim=self, duration=duration, quiet=quiet)


    def run(self, duration=None, quiet=0):

        """ Run the simulation for some duration.

        duration -- specified simulation duration (default: forever)
        quiet -- don't print StopSimulation messages (default: off)

        """

        waiters = self._waiters
        maxTime = None
        if duration:
            stop = _Waiter(None)
            stop.hasRun = 1
            maxTime = _simulator._time + duration
            schedule((maxTime, stop))
        cosim = self._cosim
        t = _simulator._time
        actives = {}

        while 1:
            try:

                for s in _siglist:
                    waiters.extend(s._update())
                del _siglist[:]

                while waiters:
                    waiter = waiters.pop()
                    if waiter.hasRun or not waiter.hasGreenLight():
                        continue
                    try:
                        clauses, clone = waiter.next()
                    except StopIteration:
                        if waiter.caller:
                            waiters.append(waiter.caller)
                        continue
                    nr = len(clauses)
                    for clause in clauses:
                        if type(clause) is _WaiterList:
                            clause.append(clone)
                            if nr > 1:
                                actives[id(clause)] = clause
                        elif isinstance(clause, Signal):
                            wl = clause._eventWaiters
                            wl.append(clone)
                            if nr > 1:
                                actives[id(wl)] = wl
                        elif type(clause) is delay:
                            schedule((t + clause._time, clone))
                        elif type(clause) is GeneratorType:
                            waiters.append(_Waiter(clause, clone))
                        elif type(clause) is join:
                            waiters.append(_Waiter(clause._generator(), clone))
                        elif clause is None:
                            waiters.append(clone)
                        else:
                            raise TypeError, "Incorrect yield clause type"

                if cosim:
                    cosim._get()
                    if _siglist or cosim._hasChange:
                        cosim._put(t)
                        continue
                elif _siglist:
                    continue

                if actives:
                    for wl in actives.values():
                        wl.purge()
                    actives = {}

                if _futureEvents:
                    if t == maxTime:
                        raise SuspendSimulation, \
                              "Simulated for duration %s" % duration
                    _futureEvents.sort()
                    t = _simulator._time = _futureEvents[0][0]
                    if cosim:
                        cosim._put(t)
                    while _futureEvents:
                        newt, event = _futureEvents[0]
                        if newt == t:
                            if type(event) is _Waiter:
                                waiters.append(event)
                            else:
                                waiters.extend(event.apply())
                            del _futureEvents[0]
                        else:
                            break
                else:
                    raise StopSimulation, "No more events"

            except SuspendSimulation:
                if not quiet:
                    printExcInfo()
                return 1

            except StopSimulation:
                if not quiet:
                    printExcInfo()
                self._finalize()
                return 0

            except:
                self._finalize()
                raise
        


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

