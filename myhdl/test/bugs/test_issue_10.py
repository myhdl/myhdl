
from myhdl import (Signal, intbv, concat)


def unsigned(width, value=0, cls=intbv):
    """Create an unsigned signal based on a bitvector with the
    specified width and initial value.
    """
    return Signal(cls(value, 0, 2 ** width))


def signed(width, value=0, cls=intbv):
    """Create an signed signal based on a bitvector with the
    specified width and initial value.
    """
    return Signal(cls(value, -2 ** (width - 1), 2 ** (width - 1)))


a = unsigned(4, 8)
b = signed(28, -3)


# print "%08X" % myhdl.concat(a, b)
# print hex(myhdl.concat(a, b))
def test_issue_10():
    assert concat(a, b) == 0x8ffffffd
