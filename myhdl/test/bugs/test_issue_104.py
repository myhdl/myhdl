import pytest
from myhdl import Simulation, always, delay, Signal, intbv, StopSimulation, SimulationError, instance, now


def test():
  @instance
  def tbstim():
    yield delay(10)
    print("{:<8d} ".format(now()))
    yield delay(1000)
    print("{:<8d} ".format(now()))
    for _ in range(10):
      yield delay(1000)

  return tbstim


def issue_104_quit_method():
    sim = Simulation(test())
    sim.run(1000)
    sim.run(500)
    sim.quit()
    return sim._finished
    
def issue_104_multiple_instance():
    sim1 = Simulation(test())
    sim1.run(1000)
    # sim1 is "puased"

    # try and create a second, third, forth simulation instance
    for ii in range(4):
        with pytest.raises(SimulationError) as excinfo:
              another_sim = Simulation(test())
        assert 'Only a single Simulation instance is allowed' in str(excinfo.value)
    # generating more sims should have failed
    sim1.run(1000)

def test_issue_104():
    assert issue_104_quit_method() == True
    issue_104_multiple_instance()

