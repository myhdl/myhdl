from __future__ import absolute_import
from myhdl import *

def issue_9():

    t_State = enum('foo', 'bar')

    assert (Signal(t_State.foo) == Signal(t_State.bar)) == False 
    assert (Signal(t_State.foo) != Signal(t_State.bar)) == True 
    assert (Signal(t_State.foo) == Signal(t_State.foo)) == True 
    assert (Signal(t_State.foo) != Signal(t_State.foo)) == False 


def test_issue_9():
    issue_9()
