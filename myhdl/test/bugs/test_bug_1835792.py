import sys
import os
path = os.path
import random
from random import randrange
random.seed(2)

import myhdl
from myhdl import *

ACTIVE_LOW, INACTIVE_HIGH = bool(0), bool(1)

@block
def bug_1835792 ():
    """ Semicolon conversion

    """
    
    @instance
    def logic():
        v = intbv(0, min=-15, max=45)
        yield delay(10)
        print(v.min);
        print(v.max);
        
    return logic


def test_bug_1835792 ():  
    assert bug_1835792().verify_convert() == 0
    
