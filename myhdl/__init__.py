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

""" doc """

__author__= "Jan Decaluwe <jan@jandecaluwe.com>"
__version__ = "$Revision$"
__date__ = "$Date$"

import Signal
import Simulation
import delay
import intbv
import _simulator

StopSimulation = Simulation.StopSimulation
join = Simulation.join
Simulation = Simulation.Simulation
posedge = Signal.posedge
negedge = Signal.negedge
Signal = Signal.Signal
now = _simulator.now
delay = delay.delay
intbv = intbv.intbv

def downrange(start, stop=0):
    return range(start-1, stop-1, -1)




