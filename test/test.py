""" Run all the myhdl unit tests. """

import unittest

from myhdl import test_all

unittest.main(defaultTest='test_all.suite',
              testRunner=unittest.TextTestRunner(verbosity=2))
