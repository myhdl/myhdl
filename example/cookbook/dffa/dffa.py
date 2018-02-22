import myhdl
from myhdl import *

def dffa(q, d, clk, rst):

    @always(clk.posedge, rst.negedge)
    def logic():
        if rst == 0:
            q.next = 0
        else:
            q.next = d

    return logic


from random import randrange

def test_dffa():
    
    q, d, clk, rst = [Signal(bool(0)) for i in range(4)]
    
    dffa_inst = dffa(q, d, clk, rst)

    @always(delay(10))
    def clkgen():
        clk.next = not clk

    @always(clk.negedge)
    def stimulus():
        d.next = randrange(2)

    @instance
    def rstgen():
        yield delay(5)
        rst.next = 1
        while True:
            yield delay(randrange(500, 1000))
            rst.next = 0
            yield delay(randrange(80, 140))
            rst.next = 1

    return dffa_inst, clkgen, stimulus, rstgen

def simulate(timesteps):
    tb = traceSignals(test_dffa)
    sim = Simulation(tb)
    sim.run(timesteps)
    sim.quit()

simulate(20000)

def convert():
    q, d, clk, rst = [Signal(bool(0)) for i in range(4)]
    toVerilog(dffa, q, d, clk, rst)
    conversion.analyze(dffa, q, d, clk, rst)
 
convert()
 


    
