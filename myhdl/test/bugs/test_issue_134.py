"""
When an interface signal gets passed into a function, it
can get renamed to the name of the argument. When the
function is called multiple times, this causes name collisions """

import pytest
import myhdl
from myhdl import *

class AB:
    def __init__(self):
        self.a = Signal(bool(False))
        self.b = Signal(bool(False))

@block
def invert(sigin, sigout):
    @always_comb
    def foo():
        sigout.next = not sigin
    return foo

@block
def issue_134(ab_in, ab_out):
    """ Instantiate an inverter for each signal """
    inverta = invert(ab_in.a, ab_out.a)
    invertb = invert(ab_in.b, ab_out.b)
    return inverta, invertb

#@pytest.mark.xfail
def test_issue_134():
    """ check for port name collision"""
    assert issue_134(AB(), AB()).analyze_convert() == 0
