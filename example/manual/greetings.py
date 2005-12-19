from myhdl import Signal, delay, instance, always, now, Simulation

def ClkDriver(clk, period=20):
    
    lowTime = int(period/2)
    highTime = period - lowTime

    @instance
    def driveClk():
        while True:
            yield delay(lowTime)
            clk.next = 1
            yield delay(highTime)
            clk.next = 0

    return driveClk
            

def Hello(clk, to="World!"):

    @always(clk.posedge)
    def sayHello():
        print "%s Hello %s" % (now(), to)

    return sayHello


def greetings():

    clk1 = Signal(0)
    clk2 = Signal(0)
    
    clkdriver_1 = ClkDriver(clk1) # positional and default association
    clkdriver_2 = ClkDriver(clk=clk2, period=19) # named association 
    hello_1 = Hello(clk=clk1) # named and default association
    hello_2 = Hello(to="MyHDL", clk=clk2) # named association

    return clkdriver_1, clkdriver_2, hello_1, hello_2


def main():
    inst = greetings()
    sim = Simulation(inst)
    sim.run(50)

if __name__ == '__main__':
    main()

