import test_Simulation, test_Signal, test_intbv
from demo.arith_lib import test_all

modules = (test_Simulation, test_Signal, test_intbv)

import unittest

tl = unittest.defaultTestLoader
def suite():
    alltests = unittest.TestSuite()
    for m in modules:
        alltests.addTest(tl.loadTestsFromModule(m))
    alltests.addTest(test_all.suite())
    return alltests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
