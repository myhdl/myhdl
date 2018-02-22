from myhdl import Signal, ResetSignal, modbv

from gray_inc_reg import gray_inc_reg

def convert_gray_inc_reg(hdl, width=8):
    graycnt = Signal(modbv(0)[width:])
    enable = Signal(bool())
    clock = Signal(bool())
    reset = ResetSignal(0, active=0, async=True)

    inst = gray_inc_reg(graycnt, enable, clock, reset, width)
    inst.convert(hdl)

convert_gray_inc_reg(hdl='Verilog')
convert_gray_inc_reg(hdl='VHDL')
