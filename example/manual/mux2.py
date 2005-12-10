from myhdl import Signal, Simulation, delay, always_comb

def Mux(z, a, b, sel):
    
    """ Multiplexer.
    
    z -- mux output
    a, b -- data inputs
    sel -- control input: select a if asserted, otherwise b
    
    """
    
    @always_comb
    def muxLogic():
        if sel == 1:
            z.next = a
        else:
            z.next = b

    return muxLogic

from random import randrange

z, a, b, sel = [Signal(0) for i in range(4)]

mux_1 = Mux(z, a, b, sel)

def test():
    print "z a b sel"
    for i in range(8):
        a.next, b.next, sel.next = randrange(8), randrange(8), randrange(2)
        yield delay(10)
        print "%s %s %s %s" % (z, a, b, sel)

test_1 = test()

def main():
    sim = Simulation(mux_1, test_1)
    sim.run()    
    
if __name__ == '__main__':
    main()
