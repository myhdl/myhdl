from __future__ import absolute_import

from myhdl import *

times_called = 0

@block
def Demonstration():
    a = Signal(False)

    @instance
    def poke_loop():
        yield delay(1)
        a.next = not a

    @always(a)
    def comb_loop():
        global times_called
        times_called += 1
        a.next = not a
        assert times_called < 1001

    return (comb_loop, poke_loop)

def test_issue_180():
    demo_inst = Demonstration()
    demo_inst.config_sim(trace=True)
    sim = Simulation(demo_inst)
    sim.run(10)
