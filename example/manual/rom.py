from myhdl import *

CONTENT = (17, 134, 52, 9)

def rom(dout, addr, CONTENT):
    """ ROM model """

    @always_comb
    def read():
        dout.next = CONTENT[int(addr)]

    return read

dout = Signal(intbv(0)[8:])
addr = Signal(intbv(0)[4:])
CONTENT = (17, 134, 52, 9)

toVerilog(rom, dout, addr, CONTENT)

