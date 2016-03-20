from math import atan, sqrt, ceil, floor, pi

import myhdl
from myhdl import *

t_State = enum("WAITING", "CALCULATING")

def SineComputer(cos_z0, sin_z0, done, z0, start, clock, reset):
    
    """ Sine and cosine computer.

    This module computes the sine and cosine of an input angle. The
    floating point numbers are represented as integers by scaling them
    up with a factor corresponding to the number of bits after the point.

    Ports:
    -----
    cos_z0: cosine of the input angle
    sin_z0: sine of the input angle
    done: output flag indicating completion of the computation
    z0: input angle; -pi/2 <= z0 <= pi/2
    start: input that starts the computation on a posedge
    clock: clock input
    reset: reset input

    """

    # angle input bit width
    W = len(z0)

    # angle input z0 represents number between -pi/2 and pi/2
    # scaling factor corresponds to the nr of bits after the point
    M = 2 ** (W-2)

    # nr of iterations equals nr of significant input bits
    N = W-1
    
    # calculate X0
    An = 1.0
    for i in range(N):
        An *= (sqrt(1 + 2**(-2*i)))
        
    # X0
    X0 = int(round(M*1/An))
    
    # tuple with elementary angles
    angles = tuple([int(round(M*atan(2**(-i)))) for i in range(N)])
    
    # iterative cordic processor
    @instance
    def processor():
        
        x = intbv(0, min=sin_z0.min, max=sin_z0.max)
        y = intbv(0, min=sin_z0.min, max=sin_z0.max)
        z = intbv(0, min=z0.min, max=z0.max)
        dx = intbv(0, min=sin_z0.min, max=sin_z0.max)
        dy = intbv(0, min=sin_z0.min, max=sin_z0.max)
        dz = intbv(0, min=z0.min, max=z0.max)
        i = intbv(0, min=0, max=N)
        state = t_State.WAITING

        while True:
            yield clock.posedge, reset.posedge

            if reset:
                state = t_State.WAITING
                cos_z0.next = 1
                sin_z0.next = 0
                done.next = False
                x[:] = 0
                y[:] = 0
                z[:] = 0
                i[:] = 0

            else:
                if state == t_State.WAITING:
                    if start:
                        x[:] = X0
                        y[:] = 0
                        z[:] = z0
                        i[:] = 0
                        done.next = False
                        state = t_State.CALCULATING

                elif state == t_State.CALCULATING:
                    dx[:] = y >> i
                    dy[:] = x >> i
                    dz[:] = angles[int(i)]
                    if (z >= 0):
                        x -= dx
                        y += dy
                        z -= dz
                    else:
                        x += dx
                        y -= dy
                        z += dz
                    if i == N-1:
                        cos_z0.next = x
                        sin_z0.next = y
                        state = t_State.WAITING
                        done.next = True
                    else:
                        i += 1

    return processor

def SineComputer_v(cos_z0, sin_z0, done, z0, start, clock, reset):
    toVerilog(SineComputer, cos_z0, sin_z0, done, z0, start, clock, reset)
    conversion.analyze(SineComputer, cos_z0, sin_z0, done, z0, start, clock, reset)
    cmd = "cver -q +loadvpi=./myhdl_vpi:vpi_compat_bootstrap " + \
          "SineComputer.v tb_SineComputer.v"
    return Cosimulation(cmd, **locals())
##     cmd = "iverilog SineComputer.v tb_SineComputer.v"
##     import os
##     os.system(cmd)
##     return Cosimulation("vvp -m ./myhdl.vpi a.out", **locals())

       

