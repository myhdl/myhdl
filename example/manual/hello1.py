from __future__ import generators
from myhdl import Signal, delay, posedge, now, Simulation

def sayHello():
    while 1:
        yield delay(10)
        print "%s Hello World!" % now()

def main():
    sim = Simulation(sayHello())
    sim.run(30)

if __name__ == '__main__':
    main()


