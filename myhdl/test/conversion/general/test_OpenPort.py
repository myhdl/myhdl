'''
Created on 19 okt. 2023

@author: josy
'''

from myhdl import (block, Signal, intbv, always_comb, always_seq, instances,
                   OpenPort)


@block
def contrived_dff(Clk, D, Q, OE):

    @always_seq(Clk.posedge, reset=None)
    def cdff():
        Q.next = D
        OE.next = Q and D

    return instances()


@block
def contrived_dff2(Clk, D, Q, OE):

    @always_seq(Clk.posedge, reset=None)
    def sdff():
        Q.next = D

    @always_comb
    def cdff():
        OE.next = Q and D

    return instances()


@block
def wrapper(Clk, D, Q):
    return contrived_dff(Clk, D, Q, OE=OpenPort())


@block
def wrapper2(Clk, D, Q):
    return contrived_dff2(Clk, D, Q, OE=OpenPort())


def test_contrived_dff2():
        Clk = Signal(bool(0))
        D = Signal(bool(0))
        Q = Signal(bool(0))
        OE = Signal(bool(0))

        assert contrived_dff(Clk, D, Q, OE).analyze_convert() == 0


def test_wrapper():
        Clk = Signal(bool(0))
        D = Signal(bool(0))
        Q = Signal(bool(0))

        assert wrapper(Clk, D, Q).analyze_convert() == 0


def test_wrapper2():
        Clk = Signal(bool(0))
        D = Signal(bool(0))
        Q = Signal(bool(0))

        assert wrapper2(Clk, D, Q).analyze_convert() == 0


if __name__ == '__main__':

    def convert():
        Clk = Signal(bool(0))
        D = Signal(bool(0))
        Q = Signal(bool(0))
        OE = Signal(bool(0))

        dfc = contrived_dff(Clk, D, Q, OE)
        dfc.convert(hdl='VHDL')
        dfc.convert(hdl='Verilog')

        dfc2 = wrapper(Clk, D, Q)
        dfc2.convert(hdl='VHDL')
        dfc2.convert(hdl='Verilog')

        dfc3 = wrapper2(Clk, D, Q)
        dfc3.convert(hdl='VHDL')
        dfc3.convert(hdl='Verilog')

    convert()

    @block
    def dff(Clk, D, Q, Q_n):

        @always_seq(Clk.posedge, reset=None)
        def sdff():
            Q.next = D
            Q_n.next = not D

        return instances()

    @block
    def wrapper_dff(Clk, D, Q):
        return dff(Clk, D, Q, Q_n=OpenPort())

    Clk = Signal(bool(0))
    D = Signal(bool(0))
    Q = Signal(bool(0))

    dfc = wrapper_dff(Clk, D, Q)
    dfc.convert(hdl='Verilog')
    dfc.convert(hdl='VHDL')

