import pytest
from myhdl import Simulation, always, delay, Signal, intbv, StopSimulation, SimulationError


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
    
def issue_104_multiple_instance():
    clk = Signal(intbv(1))
    sim = Simulation(clk_driver(clk))
    sim.run(1000)
    sim2 = Simulation(clk_driver(clk))
    sim2.run(10)

def test_issue_104():

    assert issue_104_quit_method() == True

    with pytest.raises(SimulationError) as excinfo:
        issue_104_multiple_instance()
    assert 'Only a single Simulation instance is allowed' in str(excinfo.value)


