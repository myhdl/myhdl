from random import randrange
from myhdl import block, Signal, intbv, always_comb
from myhdl.conversion import analyze
import pytest

list_of_neg = []

for random_neg in range(2):
    list_of_neg.append(randrange(-16, 0))


@block
def issue_171(a, b):

    #  Negative assignments
    s1 = Signal(intbv(list_of_neg[0], min=-16, max=0))
    s2 = Signal(intbv(list_of_neg[1], min=-16, max=0))
    s3 = Signal(intbv(0, min=-32, max=32))

    @always_comb
    def foo():

        s3.next = s1 + s2
        b.next = a

    return foo


@pytest.mark.xfail
def test_issue_171():

    a, b = [Signal(bool(0)) for _ in range(2)]
    instance = issue_171(a, b)
    instance.convert(hdl='verilog')
    analyze.simulator = 'iverilog'
    assert issue_171(a, b).analyze_convert == 0

if __name__ == '__main__':
    test_issue_171()
