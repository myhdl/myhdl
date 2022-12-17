import pytest
from myhdl import Simulation, delay, SimulationError, instance, now, block
from myhdl._Simulation import _error
from helpers import raises_kind

@block
def dut():
  @instance
  def tbstim():
    yield delay(10)
    print("{0:<8d} ".format(now()))
    yield delay(1000)
    print("{0:<8d} ".format(now()))
    for _ in range(10):
      yield delay(1000)

  return tbstim


def issue_104_quit_method():
    sim = Simulation(dut())
    sim.run(1000)
    sim.run(500)
    sim.quit()
    return sim._finished
    
def issue_104_multiple_instance():
    sim1 = Simulation(dut())
    sim1.run(1000)
    # sim1 is "puased"

    # try and create a second, third, forth simulation instance
    for ii in range(4):
        with raises_kind(SimulationError, _error.MultipleSim):
              another_sim = Simulation(dut())
    # generating more sims should have failed
    sim1.run(1000)
    sim1.quit()

def test_issue_104():

    assert issue_104_quit_method() == True
    issue_104_multiple_instance()
