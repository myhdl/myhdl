from __future__ import generators
from myhdl import Signal, delay, posedge, now, Simulation

clk = Signal(0)

def clkGen():
    while 1:
        yield delay(10)
        clk.next = 1
        yield delay(10)
        clk.next = 0

def sayHello():
    while 1:
        yield posedge(clk)
        print "%s Hello World!" % now()

def main():
    sim = Simulation(clkGen(), sayHello())
    sim.run(50)

if __name__ == '__main__':
    main()
