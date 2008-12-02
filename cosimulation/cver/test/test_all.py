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

""" Run cosimulation unit tests. """


import sys

sys.path.append("../../test")

import test_bin2gray, test_inc, test_dff

# modules = (test_inc,  )
modules = (test_bin2gray, test_inc, test_dff )

import unittest

tl = unittest.defaultTestLoader
def suite():
    alltests = unittest.TestSuite()
    for m in modules:
        alltests.addTest(tl.loadTestsFromModule(m))
    return alltests

def main():
    unittest.main(defaultTest='suite',
                  testRunner=unittest.TextTestRunner(verbosity=2))
    

if __name__ == '__main__':
    main()
