import myhdl
from myhdl import *

from bin2gray2 import bin2gray
from inc import Inc

def GrayInc(graycnt, enable, clock, reset, width):
    
    bincnt = Signal(modbv(0)[width:])
    
    inc_1 = Inc(bincnt, enable, clock, reset)
    bin2gray_1 = bin2gray(B=bincnt, G=graycnt, width=width)
    
    return inc_1, bin2gray_1


def GrayIncReg(graycnt, enable, clock, reset, width):
    
    graycnt_comb = Signal(modbv(0)[width:])
    
    gray_inc_1 = GrayInc(graycnt_comb, enable, clock, reset, width)

    @always(clock.posedge)
    def reg_1():
        graycnt.next = graycnt_comb
    
    return gray_inc_1, reg_1


def main():
    width = 8
    graycnt = Signal(modbv(0)[width:])
    enable = Signal(bool())
    clock = Signal(bool())
    reset = ResetSignal(0, active=0, async=True)

    toVerilog(GrayIncReg, graycnt, enable, clock, reset, width)
    toVHDL(GrayIncReg, graycnt, enable, clock, reset, width)

          
if __name__ == '__main__':
    main()


            
            

    

    
        


                

        


  
