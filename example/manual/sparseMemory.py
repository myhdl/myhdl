from __future__ import generators

from myhdl import Signal, Simulation, posedge, negedge, delay, StopSimulation


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
    while 1:
        yield posedge(clk)
        if not en:
            continue
        if we:
            memory[addr] = din.val
        else:
            dout.next = memory[addr]
            
        
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
    while 1:
        yield posedge(clk)
        if not en:
            continue
        if we:
            memory[addr] = din.val
        else:
            try:
                dout.next = memory[addr]
            except KeyError:
                raise Error, "Unitialized address %s" % hex(addr)


dout, din, addr, we, en, clk = args = [Signal(0) for i in range(6)]

dut = sparseMemory2(*args)

def clkGen():
    while 1:
        yield delay(10)
        clk.next = not clk

def read(address):
    yield negedge(clk)
    en.next = 1
    we.next = 0
    addr.next = address
    yield posedge(clk)
    yield delay(1)
    en.next = 0
    we.next = 0

def write(data, address):
    yield negedge(clk)
    addr.next = address
    din.next = data
    en.next = 1
    we.next = 1
    yield posedge(clk)
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
    

sim = Simulation(clkGen(), test(), dut)
    
if __name__ == "__main__":
    sim.run()
    
    
            
    
    

    



    




    


    
    
        
