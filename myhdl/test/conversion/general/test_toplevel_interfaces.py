'''
Created on 23 aug. 2018

@author: josy
'''

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
def Encoder(Clk, Reset, Encoder, Position):
    lpos = Signal(intbv(0, -2 ** 15, 2 ** 15))

    @always_seq(Clk.posedge, reset=Reset)
    def synch():
        if Encoder.zero:
            lpos.next = 0
        elif Encoder.up and not Encoder.down:
            if lpos < 2 ** 15:
                lpos.next = lpos + 1
        elif not Encoder.up and Encoder.down:
            if lpos > -2 ** 15:
                lpos.next = lpos - 1

    @always_comb
    def comb():
        Position.next = lpos

    return synch, comb


@block
def XYTable(Clk, Reset, Table, Position):
    '''
        Encoding the X,Y position of an XY Table using two Encoders
        Clk, Reset: as usual
        Table: an TableXY() object giving us the input
        Position: an Cartesian2D() object telling us the position    
    '''
    pos = Cartesian2D()
    tablex = Encoder(Clk, Reset, Table.x, pos.x)
    tablex.name = 'Table_X'
    tabley = Encoder(Clk, Reset, Table.y, pos.y)
    tabley.name = 'Table_Y'

    @always_comb
    def assign():
        Position.x.next = pos.x
        Position.y.next = pos.y

    return tablex, tabley, assign


def test_top_level_interfaces_analyze():
    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, True)
    Table = TableXY()
    Position = Cartesian2D()

    dfc = XYTable(Clk, Reset, Table, Position)
    assert dfc.analyze_convert() == 0


@block
def tb_top_level_interfaces():

    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, False)
    Table = TableXY()
    Position = Cartesian2D()

    tb_dut = XYTable(Clk, Reset, Table, Position)

    xul = tuple([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    xdl = tuple([0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1])
    yul = tuple([0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1])
    ydl = tuple([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1])

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
        yield Clk.negedge

        for i in range(len(xul)):
            yield Clk.negedge
            Table.x.up.next = xul[i]
            Table.x.down.next = xdl[i]
            Table.y.up.next = yul[i]
            Table.y.down.next = ydl[i]
            yield Clk.posedge
            print("%d: %d %d" % (i, Position.x, Position.y))

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
