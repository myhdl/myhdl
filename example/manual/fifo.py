from __future__ import generators
import sys

from myhdl import Signal, Simulation, posedge, negedge, delay, \
                  StopSimulation, join

class Error(Exception):
    pass

def fifo(dout, din, re, we, empty, full, clk, maxFilling=sys.maxint):
    
    """ Synchronous fifo model based on a list.
    
    Ports:
    dout -- data out
    din -- data in
    re -- read enable
    we -- write enable
    empty -- empty indication flag
    full -- full indication flag
    clk -- clock input

    Optional parameter:
    maxFilling -- maximum fifo filling, "infinite" by default

    """
    
    memory = []
    while 1:
        yield posedge(clk)
        if we:
            memory.insert(0, din.val)
        if re:
            dout.next = memory.pop()
        empty.next = (len(memory) == 0)
        full.next = (len(memory) == maxFilling)

        
def fifo2(dout, din, re, we, empty, full, clk, maxFilling=sys.maxint):
    
    """ Synchronous fifo model based on a list.

    Ports:
    dout -- data out
    din -- data in
    re -- read enable
    we -- write enable
    empty -- empty indication flag
    full -- full indication flag
    clk -- clock input
    
    Optional parameter:
    maxFilling -- maximum fifo filling, "infinite" by default

    """
    
    memory = []
    while 1:
        yield posedge(clk)
        if we:
            memory.insert(0, din.val)
        if re:
            try:
                dout.next = memory.pop()
            except IndexError:
                raise Error, "Underflow -- Read from empty fifo"
        empty.next = (len(memory) == 0)
        full.next = (len(memory) == maxFilling)
        if len(memory) > maxFilling:
            raise Error, "Overflow -- Max filling %s exceeded" % maxFilling


dout, din, re, we, empty, full, clk = args = [Signal(0) for i in range(7)]

dut = fifo2(dout, din, re, we, empty, full, clk, maxFilling=3)

def clkGen():
    while 1:
        yield delay(10)
        clk.next = not clk

def read():
    yield negedge(clk)
    re.next = 1
    yield posedge(clk)
    yield delay(1)
    re.next = 0

def write(data):
    yield negedge(clk)
    din.next = data
    we.next = 1
    yield posedge(clk)
    yield delay(1)
    we.next = 0

def report():
    print "dout: %s empty: %s full: %s" % (hex(dout), empty, full)
    
def test():
    yield write(0x55)
    report()
    yield write(0x77)
    report()
    yield write(0x11)
    report()
    yield join(write(0x22), read())
    report()
    yield join(write(0x33), read())
    report()
    yield read()
    report()
    yield read()
    report()
    yield read()
    report()
    yield read()
    report()
    yield read()
    raise StopSimulation

    
sim = Simulation(clkGen(), test(), dut)
    
if __name__ == "__main__":
    sim.run()
    
