from math import pi, sin, cos
import random

from myhdl import *

from SineComputer import SineComputer, SineComputer_v


def bench(N=20, nrTests=1000):

    # error margin
    D = N

    # scaling factor
    M = 2**N

    # maximum angle
    ZMAX = int(round(M*pi/2))

    # signals
    cos_z0 = Signal(intbv(0, min=-M-D, max=M+D))
    sin_z0 = Signal(intbv(0, min=-M-D, max=M+D))
    z0 = Signal(intbv(0, min=-ZMAX, max=ZMAX+1))
    done = Signal(False)
    start = Signal(False)
    clock = Signal(bool(0))
    reset = Signal(True)

    # design under test
    ## dut = SineComputer(cos_z0, sin_z0, done, z0, start, clock, reset, N)
    dut = SineComputer_v(cos_z0, sin_z0, done, z0, start, clock, reset, N)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    # test vector setup
    testAngles = [-pi/2, -pi/4, 0.0, pi/4, pi/2]
    testAngles.extend([random.uniform(-pi/2, pi/2) for i in range(nrTests)])
    testAngles.extend([random.uniform(-0.01, 0.01) for i in range(nrTests)])
    testAngles.extend([random.uniform(pi/2-0.01, pi/2) for i in range(nrTests)])
    testAngles.extend([random.uniform(-pi/2, -pi/2+0.01) for i in range(nrTests)])
    
    # actual test 
    @instance
    def check():
        yield clock.negedge
        reset.next = False
        yield clock.negedge
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
##             print "Expected"
##             print exp_cos_z0
##             print exp_sin_z0
##             print "Result"
##             print cos_z0
##             print sin_z0

        raise StopSimulation

    return dut, clockgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

# test_bench()

