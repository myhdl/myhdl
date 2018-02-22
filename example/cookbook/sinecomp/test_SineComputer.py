from math import pi, sin, cos, log
import random

import myhdl
from myhdl import *

from SineComputer import SineComputer, SineComputer_v


def bench(fractionSize, errorMargin, nrTests=100):
    
    """ Test bench for SineComputer.

    fractionSize: number of bits after the point
    errorMargin: margin for rounding errors on result
    nrTests: number of tests vectors

    """

    # scaling factor to represent floats as integers
    M = 2**fractionSize

    # maximum angle
    ZMAX = int(round(M*pi/2))
    
    # error margin shorthand
    D = errorMargin

    # signals
    cos_z0 = Signal(intbv(0, min=-D, max=M+D))
    sin_z0 = Signal(intbv(0, min=-M-D, max=M+D))
    z0 = Signal(intbv(0, min=-ZMAX, max=ZMAX+1))
    done = Signal(False)
    start = Signal(False)
    clock = Signal(bool(0))
    reset = Signal(True)

    # design under test
    # dut = SineComputer(cos_z0, sin_z0, done, z0, start, clock, reset)
    dut = SineComputer_v(cos_z0, sin_z0, done, z0, start, clock, reset)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    # test vector setup
    testAngles = [-pi/2, -pi/4, 0.0, pi/4, pi/2]
    testAngles.extend([random.uniform(-pi/2, pi/2) for i in range(nrTests)])
##     testAngles.extend([random.uniform(-0.01, 0.01) for i in range(nrTests)])
##     testAngles.extend([random.uniform(pi/2-0.01, pi/2) for i in range(nrTests)])
##     testAngles.extend([random.uniform(-pi/2, -pi/2+0.01) for i in range(nrTests)])
    
    # actual test 
    @instance
    def check():
        yield clock.negedge
        reset.next = False
        for z in testAngles:
            yield clock.negedge
            z0.next = int(round(M*z))
            start.next = True
            yield clock.negedge
            start.next = False
            yield done.posedge
            exp_cos_z0 = int(round(cos(z)*M))
            exp_sin_z0 = int(round(sin(z)*M))
            assert abs(cos_z0 - exp_cos_z0) < D
            assert abs(sin_z0 - exp_sin_z0) < D

        raise StopSimulation

    return dut, clockgen, check

def test_bench():
    fractionSize = 18
    errorMargin = fractionSize
    tb = bench(fractionSize, errorMargin)
    sim = Simulation(tb)
    sim.run()

if __name__ == '__main__':
    test_bench()
