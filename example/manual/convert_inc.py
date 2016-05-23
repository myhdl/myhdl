from myhdl import Signal, ResetSignal, modbv

from inc import inc

def convert_inc(hdl):
    """Convert inc block to Verilog or VHDL."""

    m = 8

    count = Signal(modbv(0)[m:])
    enable = Signal(bool(0))
    clock  = Signal(bool(0))
    reset = ResetSignal(0, active=0, async=True)

    inc_1 = inc(count, enable, clock, reset)

    inc_1.convert(hdl=hdl)


convert_inc(hdl='Verilog')
convert_inc(hdl='VHDL')
