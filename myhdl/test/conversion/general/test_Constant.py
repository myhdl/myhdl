'''
Created on 19 okt. 2023

@author: josy
'''
from myhdl import (block, Signal, intbv, always_comb, always_seq , Constant,
                   instances)


@block
def scramble(Pattern, A, Y):
    NBR_BITS = len(Pattern)

    @always_comb
    def dsc():
        for i in range(NBR_BITS):
            if Pattern[i]:
                Y.next[i] = not A[i]
            else:
                Y.next[i] = A[i]

    return instances()


@block
def contrived(A, Y):
    WIDTH_D = len(A)
    PAT1 = Constant(intbv(0x42)[WIDTH_D:])
    PAT2 = Constant(intbv(0xbd)[WIDTH_D:])
    y1a2 = Signal(intbv(0)[WIDTH_D:])

    s1 = scramble(PAT1, A, y1a2)
    s2 = scramble(PAT2, y1a2, Y)

    return instances()


@block
def contrived2(A, Y):
    WIDTH_D = len(A)
    PAT = [Constant(intbv(0x42)[WIDTH_D:]), Constant(intbv(0xbd)[WIDTH_D:])]
    y1a2 = Signal(intbv(0)[WIDTH_D:])

    s1 = scramble(PAT[0], A, y1a2)
    s2 = scramble(PAT[1], y1a2, Y)

    return instances()


@block
def contrived3(WIDTH_D, Sel, Y):
    import random
    random.seed('We want repeatable randomness')

    A = [Constant(intbv(random.randint(1, 2 ** WIDTH_D - 1))[WIDTH_D:]) for __ in range(8)]

    @always_comb
    def cmux():
        Y.next = A[Sel]

    return instances()


@block
def contrived4(Clk, D, CE, Q):

    @always_seq(Clk.posedge, reset=None)
    def dff():
        if CE:
            Q.next = D

    return instances()


@block
def wrappercontrived4(Clk, D, Q):
    return contrived4(Clk, D, Constant(bool(1)), Q)


def test_contrived():
    WIDTH_D = 8
    A, Y = [Signal(intbv(0)[WIDTH_D:]) for __ in range(2)]
    assert contrived(A, Y).analyze_convert() == 0


def test_contrived2():
    WIDTH_D = 8
    A, Y = [Signal(intbv(0)[WIDTH_D:]) for __ in range(2)]
    assert contrived2(A, Y).analyze_convert() == 0


def test_contrived3():
    WIDTH_D = 8
    Y = Signal(intbv(0)[WIDTH_D:])
    Sel = Signal(intbv(0)[3:])
    assert contrived3(8, Sel, Y).analyze_convert() == 0


def test_contrived4():
    Clk, D , Q = [Signal(bool(0)) for __ in range(3)]
    CE = Signal(bool(0))
    assert contrived4(Clk, D, CE, Q).analyze_convert() == 0


def test_contrived4b():
    Clk, D , Q = [Signal(bool(0)) for __ in range(3)]
    assert wrappercontrived4(Clk, D, Q).analyze_convert() == 0


if __name__ == '__main__':

    from myhdl import delay, instance, StopSimulation

    @block
    def tb_contrived():
        WIDTH_D = 8
        A, Y = [Signal(intbv(0)[WIDTH_D:]) for __ in range(2)]

        # dut = contrived(A, Y)
        dut2 = contrived2(A, Y)

        @instance
        def stimulus():
            A.next = 0x42
            yield delay(10)
            A.next = Y
            yield delay(10)
            assert Y == 0x42

            raise StopSimulation

        return instances()

    def convert():
        WIDTH_D = 8
        A, Y = [Signal(intbv(0)[WIDTH_D:]) for __ in range(2)]
        Sel = Signal(intbv(0)[3:])
        Clk, D , Q = [Signal(bool(0)) for __ in range(3)]
        CE = Signal(bool(0))

        dfc = contrived(A, Y)
        dfc.convert(hdl='VHDL')
        dfc.convert(hdl='Verilog')

        dfc2 = contrived2(A, Y)
        dfc2.convert(hdl='VHDL')
        dfc2.convert(hdl='Verilog')

        dfc3 = contrived3(WIDTH_D, Sel, Y)
        dfc3.convert(hdl='VHDL')
        dfc3.convert(hdl='Verilog')

        dfc4 = contrived4(Clk, D, CE, Q)
        dfc4.convert(hdl='VHDL')
        dfc4.convert(hdl='Verilog')

        dfc5 = wrappercontrived4(Clk, D, Q)
        dfc5.convert(hdl='VHDL', name='contrived4b')
        dfc5.convert(hdl='Verilog', name='contrived4b')

    # dft = tb_contrived()
    # dft.config_sim(trace=True)
    # dft.run_sim()
    # print("Simulation passed")

    convert()

