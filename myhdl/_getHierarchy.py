#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2016 Jan Decaluwe
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

""" myhdl _getHierarchy module.

"""

from __future__ import absolute_import

from myhdl._extractHierarchy import _Instance
from myhdl._block import _Block


class _Hierarchy(object):

    def __init__(self, name, modinst):
        self.top = modinst
        self.hierarchy = hierarchy = []
        self.absnames = absnames = {}
        _getHierarchyHelper(1, modinst, hierarchy)
        # compatibility with _extractHierarchy
        # walk the hierarchy to define relative and absolute names
        names = {}
        top_inst = hierarchy[0]
        obj, subs = top_inst.obj, top_inst.subs
        names[id(obj)] = name
        absnames[id(obj)] = name
        for inst in hierarchy:
            obj, subs = inst.obj, inst.subs
            inst.name = names[id(obj)]
            tn = absnames[id(obj)]
            for sn, so in subs:
                names[id(so)] = sn
                absnames[id(so)] = "%s_%s" % (tn, sn)
        # print (names)
        # print(absnames)


def _getHierarchy(name, modinst):
    h = _Hierarchy(name, modinst)
    return h


def _getHierarchyHelper(level, modinst, hierarchy):
    subs = [(s.name, s) for s in modinst.subs]
    inst = _Instance(level, modinst, subs, modinst.sigdict, modinst.memdict)
    hierarchy.append(inst)
    for inst in modinst.subs:
        if isinstance(inst, _Block):
            _getHierarchyHelper(level + 1, inst, hierarchy)
