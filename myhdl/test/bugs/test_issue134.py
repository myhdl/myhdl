"""
When an interface signal gets passed into a function, it
can get renamed to the name of the argument. When the
function is called multiple times, this causes name collisions """

from __future__ import absolute_import
from myhdl import *
from myhdl.conversion import verify

class AB:
    def __init__(self):
        self.a = Signal(bool(False))
        self.b = Signal(bool(False))

def invert(sigin, sigout):
    @always_comb
    def foo():
        sigout.next = not sigin
    return foo

def issue_133(ab_in, ab_out):
    """ Instantiate an inverter for each signal """
    inverta = invert(ab_in.a, ab_out.a)
    invertb = invert(ab_in.b, ab_out.b)
    return inverta, invertb

def test_issue_133():
    """ check for port name collision"""
    assert verify(issue_133, AB(), AB()) == 0