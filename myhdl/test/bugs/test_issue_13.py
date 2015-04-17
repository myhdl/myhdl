from __future__ import absolute_import
from myhdl import *
from myhdl.conversion import analyze

def issue_13(reset, clk, d, en, q):
    COSET = 0x55

    def calculateHec(header):
        """ Return hec for an ATM header, represented as an intbv.

        The hec polynomial is 1 + x + x**2 + x**8.
        """
        hec = intbv(0)[8:]

        for ii in downrange(len(header)):
            bit = header[ii]
            hec[8:] = concat(hec[7:2],
                             bit ^ hec[1] ^ hec[7],
                             bit ^ hec[0] ^ hec[7],
                             bit ^ hec[7]
                            )
        return hec ^ COSET

    @always_seq(clk.posedge, reset=reset)
    def logic():
        if en:
            q.next = calculateHec(d)

    return logic

def test_issue_13():

    reset = ResetSignal(0, active=1, async=False)
    clk   = Signal(bool(0))
    d     = Signal(intbv(0)[32:])
    en    = Signal(bool(0))
    q     = Signal(intbv(0)[8:])

    # toVHDL.numeric_ports = False

    assert analyze(issue_13, reset, clk, d, en, q) == 0 

