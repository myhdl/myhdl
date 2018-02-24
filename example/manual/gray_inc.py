from myhdl import block, Signal, modbv 

from bin2gray import bin2gray
from inc import inc

@block
def gray_inc(graycnt, enable, clock, reset, width):
    
    bincnt = Signal(modbv(0)[width:])
    
    inc_0 = inc(bincnt, enable, clock, reset)
    bin2gray_0 = bin2gray(B=bincnt, G=graycnt)
    
    return inc_0, bin2gray_0

