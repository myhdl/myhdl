import os
# import pytest
path = os.path
import unittest

from myhdl import (always_comb, TristateSignal, Signal, toVerilog, instance, delay,
                   instances, StopSimulation, Simulation)
from .util import setupCosimulation


def tristate_obuf(A, Y, OE):
    '''three-state output buffer'''

    Y_d = Y.driver()

    @always_comb
    def hdl():
        Y_d.next = A if OE else None

    return hdl


class OBuf(object):

    def __init__(self):
        self.Y = TristateSignal(True)
        self.A = Signal(False)
        self.OE = Signal(False)

    def interface(self):
        return self.A, self.Y, self.OE


def tristate_obuf_i(obuf):
    '''three-state output buffer, using interface'''

    # Caveat: A local name of the interface signals must be declared,
    #         Otherwise, _HierExtr.extract() will not add them to symdict
    #         and conversion will fail.
    IA, IY, IOE = obuf.interface()
    Y_d = IY.driver()
#     Y_d = obuf.Y.driver()

    @always_comb
    def hdl():
        Y_d.next = IA if IOE else None
#         Y_d.next = obuf.A if obuf.OE else None

    return hdl


class TestTristate(unittest.TestCase):

    def bench(self, obuf=None):
        if obuf:
            toVerilog(tristate_obuf_i, obuf)
            A, Y, OE = obuf.interface()
            inst = setupCosimulation(name='tristate_obuf_i', **toVerilog.portmap)
        else:
            Y = TristateSignal(True)
            A = Signal(True)
            OE = Signal(False)
            toVerilog(tristate_obuf, A, Y, OE)
            inst = setupCosimulation(name='tristate_obuf', **toVerilog.portmap)

        # inst = tristate_obuf(A, Y, OE)

        @instance
        def stimulus():
            yield delay(1)
            # print now(), A, OE, Y
            self.assertEqual(Y, None)

            OE.next = True
            yield delay(1)
            # print now(), A, OE, Y
            self.assertEqual(Y, A)

            A.next = not A
            yield delay(1)
            # print now(), A, OE, Y
            self.assertEqual(Y, A)

            OE.next = False
            yield delay(1)
            # print now(), A, OE, Y
            self.assertEqual(Y, None)

            raise StopSimulation

        return instances()

    def testOBuf(self):
        print(os.getcwd())
        sim = Simulation(self.bench())
        sim.run()

# #     @pytest.xfail
    def testOBufInterface(self):
        obuf = OBuf()
        sim = Simulation(self.bench(obuf))
        sim.run()


if __name__ == '__main__':
    unittest.main()
