import myhdl
from myhdl import *
from myhdl.conversion import analyze

def dff(q, d, clk):

    @always(clk.posedge)
    def logic():
        q.next = d

    return logic


from random import randrange

def test_dff():
    
    q, d, clk = [Signal(bool(0)) for i in range(3)]
    
    dff_inst = dff(q, d, clk)

    @always(delay(10))
    def clkgen():
        clk.next = not clk

    @always(clk.negedge)
    def stimulus():
        d.next = randrange(2)

    return dff_inst, clkgen, stimulus

def simulate(timesteps):
    traceSignals.timescale = "1ps"
    tb = traceSignals(test_dff)
    sim = Simulation(tb)
    sim.run(timesteps)
    sim.quit()

simulate(2000)

def convert():
    q, d, clk = [Signal(bool(0)) for i in range(3)]
    toVerilog(dff, q, d, clk)
    analyze(dff, q, d, clk)
 
convert()
    
