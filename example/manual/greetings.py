from __future__ import generators
from myhdl import Signal, delay, posedge, now, Simulation

def clkGen(clock, period=20):
    lowTime = int(period/2)
    highTime = period - lowTime
    while 1:
        yield delay(lowTime)
        clock.next = 1
        yield delay(highTime)
        clock.next = 0

def sayHello(clock, to="World!"):
    while 1:
        yield posedge(clock)
        print "%s Hello %s" % (now(), to)

def greetings():

    clk1 = Signal(0)
    clk2 = Signal(0)
    
    clkGen1 = clkGen(clk1) # positional and default association
    clkGen2 = clkGen(clock=clk2, period=19) # named assocation 
    sayHello1 = sayHello(clock=clk1) # named and default association
    sayHello2 = sayHello(to="MyHDL", clock=clk2) # named assocation

    return clkGen1, clkGen2, sayHello1, sayHello2

sim = Simulation(greetings())
sim.run(50)

