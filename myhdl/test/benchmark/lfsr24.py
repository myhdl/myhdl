from myhdl import *

def lfsr24(lfsr, enable, clock, reset):

    @always(clock.posedge, reset.posedge)
    def logic():
        if reset == 1:
            lfsr.next = 1
        else:
            if enable:
                lfsr.next[0] = lfsr[23] ^ lfsr[22] ^ lfsr[21] ^ lfsr[16]
                lfsr.next[24:1] = lfsr[23:0]

    return logic

