'''
Created on 23 aug. 2018

@author: josy
'''

from __future__ import print_function

from myhdl import Signal, intbv, block, always_comb, always_seq, ResetSignal, instance, \
                    delay, StopSimulation

# making up something sensible or even useful


class EncoderUD(object):

    def __init__(self):
        self.up = Signal(bool(0))
        self.down = Signal(bool(0))
        self.zero = Signal(bool(0))


class TableXY(object):

    def __init__(self):
        self.x = EncoderUD()
        self.y = EncoderUD()


class Cartesian2D(object):

    def __init__(self):
        self.x = Signal(intbv(0, -2 ** 15, 2 ** 15))
        self.y = Signal(intbv(0, -2 ** 15, 2 ** 15))


@block
def XYTable(Clk, Reset, Table, Position):
    '''
        Encoding the X,Y position of an XY Table using two Encoders
        Clk, Reset: as usual
        Table: an TableXY() object giving us the input
        Position: an Cartesian2D() object telling us the position    
    '''
    # we need some local counter signals
    lposx = Signal(intbv(0, -2 ** 15, 2 ** 15))
    lposy = Signal(intbv(0, -2 ** 15, 2 ** 15))

    @always_seq(Clk.posedge, reset=Reset)
    def synch():
        if Table.x.zero:
            lposx.next = 0
        elif Table.x.up:
            if lposx < 2 ** 15:
                lposx.next = lposx + 1
        elif Table.x.down:
            if lposx > -2 ** 15:
                lposx.next = lposx - 1

        if Table.y.zero:
            lposy.next = 0
        elif Table.y.up:
            if lposy < 2 ** 15:
                lposy.next = lposy + 1
        elif Table.y.down:
            if lposy > -2 ** 15:
                lposy.next = lposy - 1

    @always_comb
    def comb():
        Position.x.next = lposx
        Position.y.next = lposy

    return synch, comb


def test_top_level_interfaces_analyze():
    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, True)
    Table = TableXY()
    Position = Cartesian2D()

    dfc = XYTable(Clk, Reset, Table, Position)
    assert dfc.analyze_convert() == 0


@block
def tb_top_level_interfaces():
    import random
    random.seed = 'We want repeatable randomness :)'

    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, False)
    Table = TableXY()
    Position = Cartesian2D()

    tb_dut = XYTable(Clk, Reset, Table, Position)

    T_OPS = 32
    xup = [ Signal(bool(random.randint(0, 1))) for _ in range(T_OPS)]
    xdown = [ Signal(bool(random.randint(0, 1))) for _ in range(T_OPS)]
    yup = [ Signal(bool(random.randint(0, 1))) for _ in range(T_OPS)]
    ydown = [ Signal(bool(random.randint(0, 1))) for _ in range(T_OPS)]

    tCK = 20
    tReset = int(tCK * 3.5)

    @instance
    def tb_clk():
        Clk.next = False
        yield delay(int(tCK // 2))
        while True:
            Clk.next = not Clk
            yield delay(int(tCK // 2))

    @instance
    def tb_stim():
        Table.x.up.next = 0
        Table.x.down.next = 0
        Table.y.up.next = 0
        Table.y.down.next = 0
        Reset.next = 1
        yield delay(tReset)
        Reset.next = 0
        yield Clk.posedge

        for i in range(T_OPS):
            Table.x.up.next = xup[i]
            Table.x.down.next = xdown[i]
            Table.y.up.next = yup[i]
            Table.y.down.next = ydown[i]
            yield Clk.posedge
            print("%d %d" % (Position.x, Position.y))

        yield Clk.posedge
        Table.x.zero.next = 1
        Table.y.zero.next = 1
        yield Clk.posedge
        Table.x.zero.next = 0
        Table.y.zero.next = 0
        yield Clk.posedge
        assert Position.x == 0
        assert Position.y == 0

        raise StopSimulation

    return tb_dut, tb_clk, tb_stim


def test_top_level_interfaces_verify():
    inst = tb_top_level_interfaces()
    assert inst.verify_convert() == 0


if __name__ == '__main__':
    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, True)
    Table = TableXY()
    Position = Cartesian2D()

    dft = tb_top_level_interfaces()
    dft.run_sim()

    dfc = XYTable(Clk, Reset, Table, Position)
    dfc.name = 'XYTable'
    dfc.convert('Verilog')
    dfc.convert('VHDL')
