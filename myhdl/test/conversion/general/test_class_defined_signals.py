from myhdl import *

class HDLClass(object):

    @block
    def model(self, clock, input_interface, output_interface):

        internal_in = Signal(False)
        internal_out = Signal(False)

        @always_comb
        def assignments():
            internal_in.next = input_interface
            output_interface.next = internal_out

        @always(clock.posedge)
        def do_something():
            print('something')
            internal_out.next = internal_in.next

        return do_something, assignments

@block
def pipeline(clock, input_interface, output_interface):

    class_inst1 = HDLClass()
    class_inst2 = HDLClass()

    intermediate_interface = Signal(False)

    class_hdl_inst1 = class_inst1.model(
        clock, input_interface, intermediate_interface)

    class_hdl_inst2 = class_inst2.model(
        clock, intermediate_interface, output_interface)

    return class_hdl_inst1, class_hdl_inst2

@block
def bench():

    clk = Signal(False)
    reset = Signal(False)
    input_interface = Signal(False)
    output_interface = Signal(False)

    N = 20

    @instance
    def clkgen():

        clk.next = 0
        for n in range(N):
            yield delay(10)
            clk.next = not clk

        raise StopSimulation()

    pipeline_inst = pipeline(clk, input_interface, output_interface)

    return pipeline_inst, clkgen

def test_multiple_class_method():

    clock = Signal(False)
    reset = Signal(False)
    input_interface = Signal(False)
    output_interface = Signal(False)

    assert conversion.verify(bench()) == 0
