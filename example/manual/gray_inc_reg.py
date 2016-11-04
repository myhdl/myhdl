from myhdl import block, always_seq, Signal, modbv 

from gray_inc import gray_inc

@block
def gray_inc_reg(graycnt, enable, clock, reset, width):
    
    graycnt_comb = Signal(modbv(0)[width:])
    
    gray_inc_0 = gray_inc(graycnt_comb, enable, clock, reset, width)

    @always_seq(clock.posedge, reset=reset)
    def reg_0():
        graycnt.next = graycnt_comb
    
    return gray_inc_0, reg_0

