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

""" myhdl Error object.

This module provides the following myhdl objects:
Error -- myhdl Error exception

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"



class Error(Exception):
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        if self.__doc__ and self.arg:
            msg = self.__doc__ + ": " + str(self.arg)
        else:
            msg = self.__doc__ or self.arg
        return msg
    
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
