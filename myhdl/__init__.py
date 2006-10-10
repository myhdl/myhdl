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
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" myhdl package initialization.

This module provides the following myhdl objects:
Simulation -- simulation class
StopStimulation -- exception that stops a simulation
now -- function that returns the current time
Signal -- class to model hardware signals
delay -- callable to model delay in a yield statement
posedge -- callable to model a rising edge on a signal in a yield statement
negedge -- callable to model a falling edge on a signal in a yield statement
join -- callable to join clauses in a yield statement
intbv -- mutable integer class with bit vector facilities
downrange -- function that returns a downward range
bin -- returns a binary string representation.
       The optional width specifies the desired string
       width: padding of the sign-bit is used.
concat -- function to concat ints, bitstrings, bools, intbvs, Signals
       -- returns an intbv
instances -- function that returns all instances defined in a function
processes -- function that returns all processes defined in a function
always_comb -- function that returns an input-sensitive generator
enum -- function that returns an enumeration type
traceSignals -- function that enables signal tracing in a VCD file
toVerilog -- function that converts a design to Verilog

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

__version__ = "0.6dev2"

import sys
import warnings

class StopSimulation(Exception):
    """ Basic exception to stop a Simulation """
    pass

class _SuspendSimulation(Exception):
    """ Basic exception to suspend a Simulation """
    pass

class Error(Exception):
    def __init__(self, kind, msg="", info=""):
        self.kind = kind
        self.msg = msg
        self.info = info
    def __str__(self):
        s = "%s%s" % (self.info, self.kind)
        if self.msg:
            s += ": %s" % self.msg
        return s

class AlwaysError(Error):
    pass
class AlwaysCombError(Error):
    pass
class InstanceError(Error):
    pass
class CosimulationError(Error):
    pass
class ExtractHierarchyError(Error):
    pass
class SimulationError(Error):
    pass
class ToVerilogError(Error):
    pass
class TraceSignalsError(Error):
    pass
class ConversionError(Error):
    pass
class ToVerilogError(ConversionError):
    pass
class ToVHDLError(ConversionError):
    pass

class ConversionWarning(UserWarning):
    pass
class ToVerilogWarning(ConversionWarning):
    pass
class ToVHDLWarning(ConversionWarning):
    pass
# warnings.filterwarnings('always', r".*", ToVerilogWarning)

def showwarning(message, category, filename, lineno):
    print >> sys.stderr, "%s: %s" % (category, message)

warnings.showwarning = showwarning


from _bin import bin
from _concat import concat
from _intbv import intbv
from _join import join
from _Signal import posedge, negedge, Signal
from _simulator import now
from _delay import delay
from _util import downrange
from _Cosimulation import Cosimulation
from _Simulation import Simulation
from _misc import instances, processes
from _always_comb import always_comb
from _always import always
from _instance import instance
from _enum import enum, EnumType, EnumItemType
from _traceSignals import traceSignals

from myhdl import conversion
from conversion import toVerilog
from conversion import toVHDL


__all__ = ["bin",
           "concat",
           "intbv",
           "join",
           "posedge",
           "negedge",
           "Signal",
           "now",
           "delay",
           "downrange",
           "StopSimulation",
           "Cosimulation",
           "Simulation",
           "instances",
           "instance",
           "processes",
           "always_comb",
           "always",
           "enum",
           "EnumType",
           "EnumItemType",
           "traceSignals",
           "toVerilog",
           "toVHDL",
           "conversion"
           ]


