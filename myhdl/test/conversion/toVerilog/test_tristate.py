import os
import pytest
import unittest

from myhdl import (always_comb, TristateSignal, Signal, block, instance, delay,
                   instances, StopSimulation, Simulation)
from .util import setupCosimulation


@block
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

@block
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
            tristate_obuf_i(obuf).convert(hdl='Verilog')
            A, Y, OE = obuf.interface()
            inst = setupCosimulation(name='tristate_obuf_i', A=A, Y=Y, OE=OE)
        else:
            Y = TristateSignal(True)
            A = Signal(True)
            OE = Signal(False)
            tristate_obuf(A, Y, OE).convert(hdl='Verilog')
            inst = setupCosimulation(name='tristate_obuf', A=A, Y=Y, OE=OE)

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

    @pytest.mark.xfail
    def testOBuf(self):
        sim = Simulation(self.bench())
        sim.run()

    @pytest.mark.xfail
    def testOBufInterface(self):
        obuf = OBuf()
        sim = Simulation(self.bench(obuf))
        sim.run()


if __name__ == '__main__':
    unittest.main()
