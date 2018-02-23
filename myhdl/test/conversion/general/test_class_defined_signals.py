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

class InterfaceWithInstanceSignal(object):

    def __init__(self):

        self.internal_ins = [
            Signal(False), Signal(False), Signal(False), Signal(False)]
        self.internal_outs = [
            Signal(False), Signal(False), Signal(False), Signal(False)]

    @block
    def model(self, clock, input_interface, output_interface, index):

        internal_in = self.internal_ins[index]
        internal_out = self.internal_outs[index]

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
def different_class_pipeline(clock, input_interface, output_interface):

    class_inst1 = HDLClass()
    class_inst2 = HDLClass()

    intermediate_interface = Signal(False)

    class_hdl_inst1 = class_inst1.model(
        clock, input_interface, intermediate_interface)

    class_hdl_inst2 = class_inst2.model(
        clock, intermediate_interface, output_interface)

    return class_hdl_inst1, class_hdl_inst2

@block
def common_class_pipeline(clock, input_interface, output_interface):

    class_inst = HDLClass()

    intermediate_interface = Signal(False)
    intermediate_interface_2 = Signal(False)
    intermediate_interface_3 = Signal(False)

    class_hdl_inst1 = class_inst.model(
        clock, input_interface, intermediate_interface)

    class_hdl_inst2 = class_inst.model(
        clock, intermediate_interface, intermediate_interface_2)

    class_hdl_inst3 = class_inst.model(
        clock, intermediate_interface_2, intermediate_interface_3)

    class_hdl_inst4 = class_inst.model(
        clock, intermediate_interface_3, output_interface)

    return class_hdl_inst1, class_hdl_inst2, class_hdl_inst3, class_hdl_inst4

@block
def interface_with_method_pipeline(clock, input_interface, output_interface):

    class_inst = InterfaceWithInstanceSignal()

    intermediate_interface = Signal(False)
    intermediate_interface_2 = Signal(False)
    intermediate_interface_3 = Signal(False)

    class_hdl_inst1 = class_inst.model(
        clock, input_interface, intermediate_interface, 0)

    class_hdl_inst2 = class_inst.model(
        clock, intermediate_interface, intermediate_interface_2, 1)

    class_hdl_inst3 = class_inst.model(
        clock, intermediate_interface_2, intermediate_interface_3, 2)

    class_hdl_inst4 = class_inst.model(
        clock, intermediate_interface_3, output_interface, 3)

    return class_hdl_inst1, class_hdl_inst2, class_hdl_inst3, class_hdl_inst4

@block
def bench(class_name='different_class'):

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

    if class_name == 'common_class':
        pipeline_inst = common_class_pipeline(
            clk, input_interface, output_interface)

    elif class_name == 'interface':
        pipeline_inst = interface_with_method_pipeline(
            clk, input_interface, output_interface)

    elif class_name == 'different_class':
        pipeline_inst = different_class_pipeline(
            clk, input_interface, output_interface)

    return pipeline_inst, clkgen

def test_multiple_class_single_method():

    clock = Signal(False)
    reset = Signal(False)
    input_interface = Signal(False)
    output_interface = Signal(False)

    assert conversion.verify(bench()) == 0

def test_single_class_single_method():

    clock = Signal(False)
    reset = Signal(False)
    input_interface = Signal(False)
    output_interface = Signal(False)

    assert conversion.verify(bench(class_name='common_class')) == 0

def test_single_interface_with_single_method():

    clock = Signal(False)
    reset = Signal(False)
    input_interface = Signal(False)
    output_interface = Signal(False)

    assert conversion.verify(bench(class_name='interface')) == 0

