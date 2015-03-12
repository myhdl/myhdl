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

""" Run the unit tests for _unparse """


import unittest
from unittest import TestCase
import compiler
from myhdl._unparse import _unparse

class UnparseTest(TestCase):

    expressions = [ "a + b",
                    "a - b",
                    "(a + b)",
                    "(a - b) - ( c + d) + 1",
                    "a & b",
                    "a | b",
                    "a ^ b",
                    "a < b",
                    "a < c > 1",
                    "a == b <= c >= d != e",
                    "a // b",
                    "~c",
                    "a << b",
                    "c % d",
                    "e * f + c",
                    "not e",
                    "d or a",
                    "a and b or c and d",
                    "a ** b",
                    "a >> b",
                    "a[m:n]",
                    "a[m+1:m-2]",
                    "a[n]",
                    "+e",
                    "-f",
                    "a(b)",
                    "f(g, h, i)",
                    "f(g, h, *args)",
                    "f(g, h, **kwargs)",
                    "f(g, h, *args, **kwargs)",
                    "f.attr",
                    "f.attr + 1 * h(g[k//2:3] & b[m])"
                  ]

    def testUnparse(self):
        for expr in self.expressions:
            ast = compiler.parse(expr)
            s = _unparse(ast )
            ast_unparse = compiler.parse(s)
            self.assertEqual(str(ast), str(ast_unparse))
            
if __name__ == "__main__":
    unittest.main()
            
            
            
