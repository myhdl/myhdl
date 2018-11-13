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

""" Module that provides the Simulation class """
from __future__ import absolute_import
from __future__ import print_function

import os
from operator import itemgetter
from types import GeneratorType

from myhdl import StopSimulation, _SuspendSimulation
from myhdl import _simulator, SimulationError
from myhdl._Cosimulation import Cosimulation
from myhdl._simulator import _signals, _siglist, _futureEvents
from myhdl._Waiter import _Waiter
from myhdl._Waiter import _inferWaiter
from myhdl._Waiter import _SignalTupleWaiter
from myhdl._util import _printExcInfo
from myhdl._instance import _Instantiator
from myhdl._block import _Block

schedule = _futureEvents.append


class _error:
    pass


_error.ArgType = "Inappriopriate argument type"
_error.MultipleCosim = "Only a single cosimulator argument allowed"
_error.DuplicatedArg = "Duplicated argument"

# flatten Block objects out


def _flatten(*args):
    arglist = []
    for arg in args:
        if isinstance(arg, _Block):
            arg = arg.subs
        if isinstance(arg, (list, tuple, set)):
            for item in arg:
                arglist.extend(_flatten(item))
        else:
            arglist.append(arg)
    return arglist


_error.MultipleSim = "Only a single Simulation instance is allowed"


class Simulation(object):

    """ Simulation class.

    Methods:
    run -- run a simulation for some duration

    """
    _no_of_instances = 0

    def __init__(self, *args):
        """ Construct a simulation object.

        *args -- list of arguments. Each argument is a generator or
                 a nested sequence of generators.

        """
        _simulator._time = 0
        arglist = _flatten(*args)
        self._waiters, self._cosims = _makeWaiters(arglist)
        if Simulation._no_of_instances > 0:
            raise SimulationError(_error.MultipleSim)
        Simulation._no_of_instances += 1
        self._finished = False
        del _futureEvents[:]
        del _siglist[:]

    def _finalize(self):
        cosims = self._cosims
        if cosims:
            for cosim in cosims:
                os.close(cosim._rt)
                os.close(cosim._wf)
                cosim._child.wait()
        if _simulator._tracing:
            _simulator._tracing = 0
            _simulator._tf.close()
        # clean up for potential new run with same signals
        for s in _signals:
            s._clear()
        Simulation._no_of_instances = 0
        self._finished = True

    def quit(self):
        self._finalize()

    def run(self, duration=None, quiet=0):
        """ Run the simulation for some duration.

        duration -- specified simulation duration (default: forever)
        quiet -- don't print StopSimulation messages (default: off)

        """

        # If the simulation is already finished, raise StopSimulation immediately
        # From this point it will propagate to the caller, that can catch it.
        if self._finished:
            raise StopSimulation("Simulation has already finished")
        waiters = self._waiters
        maxTime = None
        if duration:
            stop = _Waiter(None)
            stop.hasRun = 1
            maxTime = _simulator._time + duration
            schedule((maxTime, stop))
        cosims = self._cosims
        t = _simulator._time
        actives = {}
        tracing = _simulator._tracing
        tracefile = _simulator._tf
        exc = []
        _pop = waiters.pop
        _append = waiters.append
        _extend = waiters.extend

        while 1:
            try:

                for s in _siglist:
                    _extend(s._update())
                del _siglist[:]

                while waiters:
                    waiter = _pop()
                    try:
                        waiter.next(waiters, actives, exc)
                    except StopIteration:
                        continue

                if cosims:
                    any_cosim_changes = False
                    for cosim in cosims:
                        any_cosim_changes = \
                            any_cosim_changes or cosim._hasChange
                    for cosim in cosims:
                        cosim._get()
                    if _siglist or any_cosim_changes:
                        # It should be safe to _put a cosim with no changes
                        # because _put with the same values should be
                        # idempotent. We need to _put them all here because
                        # otherwise we can desync _get/_put.
                        for cosim in cosims:
                            cosim._put(t)
                        continue
                elif _siglist:
                    continue

                if actives:
                    for wl in actives.values():
                        wl.purge()
                    actives = {}

                # at this point it is safe to potentially suspend a simulation
                if exc:
                    raise exc[0]

                # future events
                if _futureEvents:
                    if t == maxTime:
                        raise _SuspendSimulation(
                            "Simulated %s timesteps" % duration)
                    _futureEvents.sort(key=itemgetter(0))
                    t = _simulator._time = _futureEvents[0][0]
                    if tracing:
                        print("#%s" % t, file=tracefile)
                    if cosims:
                        for cosim in cosims:
                            cosim._put(t)
                    while _futureEvents:
                        newt, event = _futureEvents[0]
                        if newt == t:
                            if isinstance(event, _Waiter):
                                _append(event)
                            else:
                                _extend(event.apply())
                            del _futureEvents[0]
                        else:
                            break
                else:
                    raise StopSimulation("No more events")

            except _SuspendSimulation:
                if not quiet:
                    _printExcInfo()
                if tracing:
                    tracefile.flush()
                return 1

            except StopSimulation:
                if not quiet:
                    _printExcInfo()
                self._finalize()
                self._finished = True
                return 0

            except Exception as e:
                if tracing:
                    tracefile.flush()
                # if the exception came from a yield, make sure we can resume
                if exc and e is exc[0]:
                    pass  # don't finalize
                else:
                    self._finalize()
                # now reraise the exepction
                raise


def _makeWaiters(arglist):
    waiters = []
    ids = set()
    cosims = []
    for arg in arglist:
        if isinstance(arg, GeneratorType):
            waiters.append(_inferWaiter(arg))
        elif isinstance(arg, _Instantiator):
            waiters.append(arg.waiter)
        elif isinstance(arg, Cosimulation):
            cosims.append(arg)
            waiters.append(_SignalTupleWaiter(arg._waiter()))
        elif isinstance(arg, _Waiter):
            waiters.append(arg)
        elif arg == True:
            pass
        else:
            raise SimulationError(_error.ArgType, str(type(arg)))
        if id(arg) in ids:
            raise SimulationError(_error.DuplicatedArg)
        ids.add(id(arg))
    # add waiters for shadow signals
    for sig in _signals:
        if hasattr(sig, '_waiter'):
            waiters.append(sig._waiter)
    return waiters, cosims
