from math import atan, sqrt, ceil, floor, pi

from myhdl import *

t_State = enum("WAITING", "CALCULATING")

def SineComputer(cos_z0, sin_z0, done, z0, start, clock, reset, N=16):
    
    # calculate x0
    An = 1.0
    for i in range(N):
        An *= (sqrt(1 + 2**(-2*i)))

    # scaling factor
    M = 2**N

    # X0
    X0 = int(round(M*1/An))
    
    # tuple with elementary angles
    angles = tuple([int(round(M*atan(2**(-i)))) for i in range(N)])

    # maximal angle
    ZMAX = int(round(M*pi/2))

    # iterative cordic processor
    @instance
    def processor():
        
        x = intbv(0, min=-M-N, max=M+N)
        y = intbv(0, min=-M-N, max=M+N)
        z = intbv(0, min=-ZMAX, max=ZMAX+1)
        dx = intbv(0, min=-M, max=M+1)
        dy = intbv(0, min=-M, max=M+1)
        dz = intbv(0, min=-ZMAX, max=ZMAX)
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
    cmd = "cver -q +loadvpi=myhdl_vpi:vpi_compat_bootstrap " + \
          "SineComputer.v tb_SineComputer.v"
    return Cosimulation(cmd, **locals())


def convert(N=16):

    # scaling factor
    M = 2**N
    
    # maximal angle
    ZMAX = int(round(M*pi/2))
    
    cos_z0 = Signal(intbv(0, min=-M, max=M+N))
    sin_z0 = Signal(intbv(0, min=-M, max=M+1))
    z0 = Signal(intbv(0, min=-ZMAX, max=ZMAX+1))
    done = Signal(False)
    start = Signal(False)
    clock = Signal(bool(0))
    reset = Signal(True)

    toVerilog(SineComputer, cos_z0, sin_z0, done, z0, start, clock, reset, N)

convert(20)
    
        


    
