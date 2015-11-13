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

""" Module that provides the Factory class and related objects.

This module provides the following objects:

MyHdlFactory -- class for the factory, which will contain 
	the static methods for generating Signals. It may 
	provide cleaner generation of Signals.
"""
from __future__ import absolute_import
from __future__ import print_function

from inspect import currentframe, getouterframes
from copy import copy, deepcopy
import operator

from myhdl._compat import integer_types, long
from myhdl import _simulator as sim
from myhdl._simulator import _signals, _siglist, _futureEvents, now
from myhdl._intbv import intbv
from myhdl._bin import bin
from myhdl._Signal import Signal



class MyHdlFactory:
	@staticmethod
	def GetSignalIntbv(val=0,bitwidth=1):
		return Signal(intbv(0)[bitwidth:])

	@staticmethod
	def GetSignalBool(boolVal):
		return Signal(bool(boolVal))
		
	# TODO in progress

