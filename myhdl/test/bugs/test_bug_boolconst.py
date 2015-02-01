from __future__ import absolute_import
from myhdl import *

INT_CONDITION_0 = 0 
INT_CONDITION_1 = 1 
BOOL_CONDITION_0 = False 
BOOL_CONDITION_1 = True 

def bug_boolconst(sigin, sigout):

    @always_comb
    def output():
        sigout.next = 0
        if INT_CONDITION_0:
            sigout.next = sigin
        if BOOL_CONDITION_0:
            sigout.next = sigin
        if not INT_CONDITION_0:
            sigout.next = sigin
        if not BOOL_CONDITION_0:
            sigout.next = sigin
        if INT_CONDITION_1:
            sigout.next = sigin
        if BOOL_CONDITION_1:
            sigout.next = sigin
        if not INT_CONDITION_1:
            sigout.next = sigin
        if not BOOL_CONDITION_1:
            sigout.next = sigin

    return output

def test_bug_boolconst():
    sigin = Signal(bool())
    sigout = Signal(bool())

    assert conversion.analyze(bug_boolconst, sigin, sigout) == 0


