from __future__ import generators
from __future__ import print_function

from myhdl import Signal, Simulation, Cosimulation
from myhdl import delay, intbv, now

import os
cmd = "iverilog -o tb_test.o ./tb_test.v "
os.system(cmd)
      
a = Signal(intbv(1))
b = Signal(intbv(2))
c = Signal(intbv(3))

cosim = Cosimulation("vvp -v -m ../myhdl.vpi tb_test.o", a=a, b=b, c=c)

def stimulus(a, b):
    for i in range(10):
        yield delay(10)
        # print "Python a=%s b=%s" % (a, b)
        a.next = a + 1
        b.next = b + 2

def response(c):
    while 1:
        yield c
        print("Python: %s %s %s %s" % (now(), c, a, b))

sim = Simulation(stimulus(a=a, b=b), response(c=c), cosim)
sim.run()


    
    
