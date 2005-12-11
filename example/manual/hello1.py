from myhdl import Signal, delay, always, now, Simulation

def HelloWorld():

    interval = delay(10)
    
    @always(interval)
    def sayHello():
        print "%s Hello World!" % now()

    return sayHello


def main():
    inst = HelloWorld()
    sim = Simulation(inst)
    sim.run(30)
    

if __name__ == '__main__':
    main()


