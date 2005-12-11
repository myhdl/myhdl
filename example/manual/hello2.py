from myhdl import Signal, delay, always, now, Simulation

def ClkDriver(clk):

    halfPeriod = delay(10)

    @always(halfPeriod)
    def driveClk():
        clk.next = not clk

    return driveClk


def HelloWorld(clk):
    
    @always(clk.posedge)
    def sayHello():
        print "%s Hello World!" % now()

    return sayHello



def main():
    clk = Signal(0)
    clkdriver_inst = ClkDriver(clk)
    hello_inst = HelloWorld(clk)
    sim = Simulation(clkdriver_inst, hello_inst)
    sim.run(50)

if __name__ == '__main__':
    main()
