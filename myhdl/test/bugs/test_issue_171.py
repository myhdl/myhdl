from random import randrange
from myhdl import *
from myhdl.conversion import analyze

list_of_neg = []

for random_neg in range(2):
    list_of_neg.append(randrange(-16, 0))


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


def test_issue_171():

    a, b = [Signal(bool(0)) for _ in range(2)]
    assert analyze(issue_171, a, b) == 0

if __name__ == '__main__':
    test_issue_171()
