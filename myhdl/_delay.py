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

""" Module that provides the delay class."""
from __future__ import absolute_import

from myhdl._compat import integer_types

_errmsg = "arg of delay constructor should be a natural integeer"


class delay(object):

    """ Class to model delay in yield statements. """

    def __init__(self, val):
        """ Return a delay instance.

        Required parameters:
        val -- a natural integer representing the desired delay

        """
        if not isinstance(val, integer_types) or val < 0:
            raise TypeError(_errmsg)
        self._time = val
