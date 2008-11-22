from myhdl import *

def inc_comb(nextCount, count, n):

    @always(count)
    def logic():
        # do nothing here
        pass

    nextCount.driven = "wire"

    __verilog__ =\
"""
assign %(nextCount)s = (%(count)s + 1) %% %(n)s;
"""

    __vhdl__ =\
"""
%(nextCount)s <= (%(count)s + 1) mod %(n)s;
"""

    return logic



def main():
    m = 8
    n = 2 ** m
    count = Signal(intbv(0)[m:])
    nextCount = Signal(intbv(0)[m:])
    toVerilog(inc_comb, nextCount, count, n)
    toVHDL(inc_comb, nextCount, count, n)

        
if __name__ == '__main__':
    main()


            
            

    

    
        


                

        

