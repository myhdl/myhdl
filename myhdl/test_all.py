import test_Simulation, test_Signal, test_intbv

modules = (test_Simulation, test_Signal, test_intbv)

import unittest

tl = unittest.defaultTestLoader
def suite():
    alltests = unittest.TestSuite()
    for m in modules:
        alltests.addTest(tl.loadTestsFromModule(m))
    return alltests

if __name__ == '__main__':
    unittest.main(defaultTest='suite',
                  testRunner=unittest.TextTestRunner(verbosity=2))
