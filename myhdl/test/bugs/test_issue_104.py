import pytest
from myhdl import Simulation, always, delay, Signal, intbv, StopSimulation


def clk_driver(clk, period=20):
        @always(delay(period/2))
        def drive_clk():
            clk.next = not clk
        return drive_clk

def issue_104_quit_method():
    clk = Signal(intbv(1))
    sim = Simulation(clk_driver(clk))
    sim.run(1000)
    sim.run(500)
    sim.quit()
    return sim._finished
sim2 = None
def issue_104_multiple_instance():
    global sim2
    clk = Signal(intbv(1))
    sim = Simulation(clk_driver(clk))
    sim.run(1000)
    sim2 = Simulation(clk_driver(clk))
    sim2.run(10)

def test_issue_104():

    assert issue_104_quit_method() == True

    with pytest.raises(StopSimulation) as excinfo:
        issue_104_multiple_instance()
    assert 'Previous Simulation is still running' in str(excinfo.value)
    sim2.quit()