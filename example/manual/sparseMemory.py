import traceback

import myhdl
from myhdl import *


class Error(Exception):
    pass

def sparseMemory(dout, din, addr, we, en, clk):
    
    """ Sparse memory model based on a dictionary.

    Ports:
    dout -- data out
    din -- data in
    addr -- address bus
    we -- write enable: write if 1, read otherwise
    en -- interface enable: enabled if 1
    clk -- clock input
    
    """
    
    memory = {}

    @always(clk.posedge)
    def access():
        if en:
            if we:
                memory[addr.val] = din.val
            else:
                 dout.next = memory[addr.val]

    return access
            
        
def sparseMemory2(dout, din, addr, we, en, clk):
    
    """ Sparse memory model based on a dictionary.

    Ports:
    dout -- data out
    din -- data in
    addr -- address bus
    we -- write enable: write if 1, read otherwise
    en -- interface enable: enabled if 1
    clk -- clock input
    
    """
    
    memory = {}

    @always(clk.posedge)
    def access():
        if en:
            if we:
                memory[addr.val] = din.val
            else:
                try:
                    dout.next = memory[addr.val]
                except KeyError:
                    raise Error, "Uninitialized address %s" % hex(addr)

    return access


dout, din, addr, we, en, clk = args = [Signal(0) for i in range(6)]

dut = sparseMemory2(*args)

def clkGen():
    while 1:
        yield delay(10)
        clk.next = not clk

def read(address):
    yield clk.negedge
    en.next = 1
    we.next = 0
    addr.next = address
    yield clk.posedge
    yield delay(1)
    en.next = 0
    we.next = 0

def write(data, address):
    yield clk.negedge
    addr.next = address
    din.next = data
    en.next = 1
    we.next = 1
    yield clk.posedge
    en.next = 0
    we.next = 0
    
def test():
    yield write(0x55, 0x55)
    yield write(0x77, 0x77)
    yield write(0x111, 0x111)
    yield read(0x77)
    print hex(dout)
    yield read(0x55)
    print hex(dout)
    yield read(0x33)
    raise StopSimulation

sim = Simulation(clkGen(), test(), dut)
    
def main():
    try:
        sim.run()
    except:
        traceback.print_exc()
    
if __name__ == '__main__':
    main()
            
    
    

    



    




    


    
    
        
