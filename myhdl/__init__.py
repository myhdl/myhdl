import Signal
import Simulation
import delay
import intbv
import _simulator

# sig = sig.sig
StopSimulation = Simulation.StopSimulation
join = Simulation.join
Simulation = Simulation.Simulation
posedge = Signal.posedge
negedge = Signal.negedge
Signal = Signal.Signal
now = _simulator.now
delay = delay.delay
intbv = intbv.intbv

def downrange(start, stop=0):
    return range(start-1, stop-1, -1)




