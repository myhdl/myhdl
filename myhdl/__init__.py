#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2015 Jan Decaluwe
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
StopSimulation -- exception that stops a simulation
now -- function that returns the current time
Signal -- factory function to model hardware signals
SignalType -- Signal base class
ConcatSignal --  factory function that models a concatenation shadow signal
TristateSignal -- factory function that models a tristate shadow signal
delay -- callable to model delay in a yield statement
posedge -- callable to model a rising edge on a signal in a yield statement
negedge -- callable to model a falling edge on a signal in a yield statement
join -- callable to join clauses in a yield statement
intbv -- mutable integer class with bit vector facilities
modbv -- modular bit vector class
downrange -- function that returns a downward range
bin -- returns a binary string representation.
       The optional width specifies the desired string
       width: padding of the sign-bit is used.
concat -- function to concat ints, bitstrings, bools, intbvs, Signals
       -- returns an intbv
instances -- function that returns all instances defined in a function
always --
always_comb -- decorator that returns an input-sensitive generator
always_seq --
ResetSignal --
enum -- function that returns an enumeration type
traceSignals -- function that enables signal tracing in a VCD file
toVerilog -- function that converts a design to Verilog

"""
from __future__ import absolute_import
from __future__ import print_function

__version__ = "0.11"


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


class BlockError(Error):
    pass


class BlockInstanceError(Error):
    pass


class CosimulationError(Error):
    pass


class ExtractHierarchyError(Error):
    pass


class SimulationError(Error):
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

# def showwarning(message, category, filename, lineno, *args):
#    print("** %s: %s" % (category.__name__, message), file=sys.stderr)

#warnings.showwarning = showwarning


from ._bin import bin
from ._concat import concat
from ._intbv import intbv
from ._modbv import modbv
from ._join import join
from ._Signal import posedge, negedge, Signal, SignalType
from ._ShadowSignal import ConcatSignal
from ._ShadowSignal import TristateSignal
from ._simulator import now
from ._delay import delay
from ._Cosimulation import Cosimulation
from ._Simulation import Simulation
from ._misc import instances, downrange
from ._always_comb import always_comb
from ._always_seq import always_seq, ResetSignal
from ._always import always
from ._instance import instance
from ._block import block, lightblock
from ._enum import enum, EnumType, EnumItemType
from ._traceSignals import traceSignals

from myhdl import conversion
from .conversion import toVerilog
from .conversion import toVHDL

from ._tristate import Tristate


__all__ = ["bin",
           "concat",
           "intbv",
           "modbv",
           "join",
           "posedge",
           "negedge",
           "Signal",
           "SignalType",
           "ConcatSignal",
           "TristateSignal",
           "now",
           "delay",
           "downrange",
           "StopSimulation",
           "Cosimulation",
           "Simulation",
           "instances",
           "instance",
           "block",
           "lightblock",
           "always_comb",
           "always_seq",
           "ResetSignal",
           "always",
           "enum",
           "EnumType",
           "EnumItemType",
           "traceSignals",
           "toVerilog",
           "toVHDL",
           "conversion",
           "Tristate"
           ]
