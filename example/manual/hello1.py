from myhdl import block, delay, always, now

@block
def HelloWorld():

    @always(delay(10))
    def say_hello():
        print("%s Hello World!" % now())

    return say_hello


inst = HelloWorld()
inst.run_sim(30)
