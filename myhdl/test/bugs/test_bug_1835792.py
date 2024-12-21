import os
path = os.path
import random
random.seed(2)

from myhdl import (block, intbv, instance, delay)

ACTIVE_LOW, INACTIVE_HIGH = bool(0), bool(1)


@block
def bug_1835792 ():
    """ Semicolon conversion

    """

    @instance
    def comb():
        v = intbv(0, min=-15, max=45)
        yield delay(10)
        print(v.min);
        print(v.max);

    return comb


def test_bug_1835792 ():
    assert bug_1835792().verify_convert() == 0

