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

import _simulator
from _simulator import _siglist, _futureEvents
from Signal import Signal, _SignalWrap, _WaiterList
from delay import delay
from types import GeneratorType
from join import join
from _Waiter import _Waiter
from util import StopSimulation, SuspendSimulation

schedule = _futureEvents.append


def run(sim, duration=None, quiet=0):

    """ Run the simulation for some duration.

    duration -- specified simulation duration (default: forever)
    quiet -- don't print StopSimulation messages (default: off)

    """

    waiters = sim._waiters
    maxTime = None
    if duration:
        stop = _Waiter(None)
        stop.hasRun = 1
        maxTime = _simulator._time + duration
        schedule((maxTime, stop))
    cosim = sim._cosim
    t = _simulator._time
    actives = {}

    while 1:
        try:

            for s in _siglist:
                waiters.extend(s._update())
            del _siglist[:]

            while waiters:
                waiter = waiters.pop(0)
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
            sim._finalize()
            return 0

        except:
            sim._finalize()
            raise


