from __future__ import absolute_import
#! /usr/bin/env python

from myhdl import *

def mpegChannel(clk, rst):

    s_tx_data_xor_mask_r = Signal(intbv(0)[1 + 31:])

    @always_seq(clk.posedge, rst)
    def fsm_seq():
        for i in range(4):
            if i == 0:
                s_tx_data_xor_mask_r.next[1 + 7:0] = 0
            elif i == 1:
                s_tx_data_xor_mask_r.next[1 + 15:8] = 1
            elif i == 2:
                s_tx_data_xor_mask_r.next[1 + 23:16] = 2
            else:
                s_tx_data_xor_mask_r.next[1 + 31:24] = 3

    return instances()



def test_issue_40():
    clk = Signal(bool(0))
    rst = ResetSignal(0, active=1, async=True)

    assert conversion.analyze(mpegChannel, clk, rst) == 0


