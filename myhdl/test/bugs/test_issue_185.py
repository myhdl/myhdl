from myhdl import *

def shift_left(c, a, b):
    c.next = a << b

@block
def shifter(reset, clock, opa, opb, result):
    
    @always_seq(clock.posedge, reset = reset)
    def assign():
        shift_left(result, opa, opb)

    return assign


def convert():

    clock = Signal(bool(0))
    reset = ResetSignal(0, active=True, isasync=True)

    opa = Signal(intbv(0)[4:])
    opb = Signal(intbv(0)[4:])
    result = Signal(intbv(0)[10:])

    inst = shifter(reset, clock, opa, opb, result)
    inst.convert(hdl='VHDL')


if __name__ == '__main__':
    convert()
