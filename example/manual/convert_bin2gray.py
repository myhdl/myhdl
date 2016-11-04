from myhdl import Signal, intbv

from bin2gray import bin2gray

def convert(hdl, width=8):

    B = Signal(intbv(0)[width:])
    G = Signal(intbv(0)[width:])

    inst = bin2gray(B, G)
    inst.convert(hdl=hdl)


convert(hdl='Verilog')
convert(hdl='VHDL')
