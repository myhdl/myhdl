import myhdl
from myhdl import *

def inc_comb(nextCount, count, n):

    @always(count)
    def logic():
        # do nothing here
        pass

    nextCount.driven = "wire"

    return logic

inc_comb.verilog_code =\
"""
assign $nextCount = ($count + 1) % $n;
"""

inc_comb.vhdl_code =\
"""
$nextCount <= ($count + 1) mod $n;
"""




def main():
    m = 8
    n = 2 ** m
    count = Signal(intbv(0)[m:])
    nextCount = Signal(intbv(0)[m:])
    toVerilog(inc_comb, nextCount, count, n)
    toVHDL(inc_comb, nextCount, count, n)

        
if __name__ == '__main__':
    main()


            
            

    

    
        


                

        

