from __future__ import absolute_import
import sys
import os
path = os.path
import random
from random import randrange
random.seed(2)

from myhdl import *
from myhdl.conversion import verify


ACTIVE_LOW, INACTIVE_HIGH = bool(0), bool(1)

def bug_1835797():
    """ Docstring in the middle.

    """
    
    @instance
    def logic():
        v = intbv(0, min=-15, max=45)
        """Wrongly placed docstring"""
        yield delay(10)
        print(v.min)
        print(v.max)
        
    return logic


def test_bug_1835797():  
    assert verify(bug_1835797) == 0
    
