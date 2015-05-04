from random import randrange
from pytest import raises
from myhdl import *

from myhdl import Signal, Simulation, instances, now

from myhdl._always_seq import always_seq, _AlwaysSeq, _error, AlwaysSeqError



def test_clock():
    """ check the edge parameter """

    # should fail without a valid Signal
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)

    with raises(AlwaysSeqError) as e:
        @always_seq(clock, reset=reset)
        def logic1():
            pass
        assert e.kind == _error.EdgeType

    # should work with a valid Signal
    clock = Signal(bool(0))
    try:
        @always_seq(clock.posedge, reset=reset)
        def logic2():
            pass
    except:
        assert False

def test_reset(): 
    """ check the reset parameter """
    
    # should fail without a valid ResetSignal
    clock = Signal(bool(0))
    reset = Signal(bool(0))

    with raises(AlwaysSeqError) as e:
        @always_seq(clock.posedge, reset=reset)
        def logic():
            pass
        assert e.kind == _error.ResetType

    # should work with a valid Signal
    reset = ResetSignal(0, active=0, async=True)
    try:
        @always_seq(clock.posedge, reset=reset)
        def logic2():
            pass
    except:
        assert False

