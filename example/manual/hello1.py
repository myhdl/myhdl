from __future__ import generators
from myhdl import Signal, delay, posedge, now, Simulation

def sayHello():
    while 1:
        yield delay(10)
        print "%s Hello World!" % now()

sim = Simulation(sayHello())
sim.run(30)

