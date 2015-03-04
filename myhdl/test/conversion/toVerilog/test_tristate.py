import os
path = os.path
import unittest

from myhdl import *
from util import setupCosimulation

def tristate_obuf(A, Y, OE):
    '''three-state output buffer'''

    Y_d = Y.driver()
    @always_comb
    def hdl():
        Y_d.next = A if OE else None

    return hdl

def tristate_obuf_v(name, A, Y, OE):
    return setupCosimulation(**locals())

class TestTristate(unittest.TestCase):
    def bench(self):
        Y  = TristateSignal(True)
        Y_d = Y.driver()
        A  = Signal(True)
        OE = Signal(False)

        toVerilog(tristate_obuf, A, Y, OE)
        inst = tristate_obuf_v(tristate_obuf.func_name, A, Y_d, OE)
        #inst = tristate_obuf(A, Y, OE)

        @instance
        def stimulus():
            yield delay(1)
            #print now(), A, OE, Y
            self.assertEqual(Y, None)

            OE.next = True
            yield delay(1)
            #print now(), A, OE, Y
            self.assertEqual(Y, A)

            A.next = not A
            yield delay(1)
            #print now(), A, OE, Y
            self.assertEqual(Y, A)

            raise StopSimulation
        return instances()


    def testOBuf(self):
        sim = Simulation(self.bench())
        sim.run()

if __name__ == '__main__':
    unittest.main()
