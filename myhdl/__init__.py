import Signal
import Simulation
import delay
import intbv
import _simulator

# sig = sig.sig
posedge = Signal.posedge
negedge = Signal.negedge
# DelayedSignal = Signal.DelayedSignal
Signal = Signal.Signal
join = Simulation.join
StopSimulation = Simulation.StopSimulation
Simulation = Simulation.Simulation
now = _simulator.now
delay = delay.delay
concat = intbv.concat
intbv = intbv.intbv

def downrange(start, stop=0):
    return range(start-1, stop-1, -1)




