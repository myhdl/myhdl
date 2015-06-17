
import unittest
from myhdl import *
from random import randrange

import os

veriutils_available = True
try:
    from veriutils import (
        vivado_verilog_cosimulation, vivado_vhdl_cosimulation, 
        myhdl_cosimulation, copy_signal, VIVADO_EXECUTABLE)

except ImportError:
    veriutils_available = False

# The config files are in the same dir as this file
_config_path = os.path.split(__file__)[0]
_config_file = os.path.join(_config_path, 'veriutils.cfg')
_template_prefix = _config_path

def trivial(input_signal, output_signal, clock):

    @always(clock.posedge)
    def trivial_instance():

        output_signal.next = input_signal

    return trivial_instance

@unittest.skipIf(not veriutils_available, 'Veriutils cannot be imported.')
@unittest.skipIf(VIVADO_EXECUTABLE is None, 'Vivado executable not in path')
class InitialValueTestMixin(object):

    def cosimulate(self, *args, **kwargs):
        raise NotImplementedError

    def setUp(self):
        self._verilog_disable_initial_value = toVerilog.disable_initial_value
        self._vhdl_disable_initial_value = toVHDL.disable_initial_value

        toVerilog.disable_initial_value = False
        toVHDL.disable_initial_value = False

        self.args = {'clock': Signal(False)}
        self.arg_types = {'input_signal': 'custom',
                          'output_signal': 'output',
                          'clock': 'clock'}

    def tearDown(self):
        toVerilog.disable_initial_value = self._verilog_disable_initial_value
        toVHDL.disable_initial_value = self._vhdl_disable_initial_value

    def test_unsigned(self):
        '''The correct initial value should be used for unsigned type signal.

        The initial value should be derived from the _init attribute of the 
        signal.
        '''

        min_val = 0
        max_val = 35

        self.args['input_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                 min=min_val, max=max_val))
        self.args['output_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                  min=min_val, max=max_val))

        test_cycles = 10

        expected_outputs = (
            [int(self.args['output_signal']._init)] + 
            [int(self.args['input_signal']._init)] * (test_cycles - 1))

        dut_signals, ref_signals = self.cosimulate(
            test_cycles, trivial, trivial, self.args, self.arg_types, 
            config_file=_config_file, template_path_prefix=_template_prefix)

        self.assertTrue(ref_signals['output_signal'] == expected_outputs)        
        self.assertTrue(dut_signals['output_signal'] == expected_outputs)

    def test_signed(self):
        '''The correct initial value should be used for a signed type signal.

        The initial value should be derived from the _init attribute of the 
        signal.
        '''

        min_val = -12
        max_val = 4

        self.args['input_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                 min=min_val, max=max_val))
        self.args['output_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                  min=min_val, max=max_val))

        test_cycles = 10

        expected_outputs = (
            [int(self.args['output_signal']._init)] + 
            [int(self.args['input_signal']._init)] * (test_cycles - 1))

        dut_signals, ref_signals = self.cosimulate(
            test_cycles, trivial, trivial, self.args, self.arg_types, 
            config_file=_config_file, template_path_prefix=_template_prefix)

        self.assertTrue(ref_signals['output_signal'] == expected_outputs)        
        self.assertTrue(dut_signals['output_signal'] == expected_outputs)

    def test_long_signals(self):
        '''The correct initial value should work with wide bitwidths.

        Specifically, it should not suffer from problems in which number
        must fit into a specific bitwidth (e.g. 32-bit integers)
        '''

        # Use a 72-bit signed intbv (bigger than a 32- or 64-bit integer)
        min_val = -(2**71)
        max_val = 2**71 - 1

        self.args['input_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                 min=min_val, max=max_val))
        self.args['output_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                  min=min_val, max=max_val))

        test_cycles = 10

        expected_outputs = (
            [int(self.args['output_signal']._init)] + 
            [int(self.args['input_signal']._init)] * (test_cycles - 1))

        dut_signals, ref_signals = self.cosimulate(
            test_cycles, trivial, trivial, self.args, self.arg_types, 
            config_file=_config_file, template_path_prefix=_template_prefix)

        self.assertTrue(ref_signals['output_signal'] == expected_outputs)        
        self.assertTrue(dut_signals['output_signal'] == expected_outputs)

    def test_boolean(self):
        '''The correct initial value should be used for a boolean type signal.

        The initial value should be derived from the _init attribute of the 
        signal.
        '''

        self.args['input_signal'] = Signal(False)
        self.args['output_signal'] = Signal(True)

        test_cycles = 10

        expected_outputs = (
            [bool(self.args['output_signal']._init)] + 
            [bool(self.args['input_signal']._init)] * (test_cycles - 1))

        dut_signals, ref_signals = self.cosimulate(
            test_cycles, trivial, trivial, self.args, self.arg_types, 
            config_file=_config_file, template_path_prefix=_template_prefix)

        self.assertTrue(ref_signals['output_signal'] == expected_outputs)        
        self.assertTrue(dut_signals['output_signal'] == expected_outputs)

    def test_init_used(self):
        '''It should be the _init attribute that is used for initialisation

        It should not be the current value, which should be ignored.
        '''

        min_val = -12
        max_val = 4

        self.args['input_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                 min=min_val-1, max=max_val))
        self.args['output_signal'] = Signal(intbv(randrange(min_val, max_val), 
                                                  min=min_val-1, max=max_val))

        test_cycles = 10

        expected_outputs = (
            [int(self.args['output_signal']._init)] + 
            [int(self.args['input_signal']._init)] * (test_cycles - 1))

        # Get the reference pre-hackery
        _, ref_signals = myhdl_cosimulation(
            test_cycles, trivial, trivial, self.args, self.arg_types)

        # Currently we're actually testing veriutils, not the conversion
        # code...
#        import veriutils
#        def wrapped_Simulation(*args, **kwargs):
#            result = Simulation(*args, **kwargs)
#
#            self.args['input_signal']._val = (
#                self.args['input_signal'].val - 1)
#            self.args['output_signal']._val = (
#                self.args['output_signal'].val - 1)
#
#            return result

#        veriutils.cosimulation.Simulation = wrapped_Simulation

        dut_signals, _ = self.cosimulate(
            test_cycles, trivial, trivial, self.args, self.arg_types, 
            config_file=_config_file, template_path_prefix=_template_prefix)

#        veriutils.cosimulation.Simulation = Simulation

        self.assertTrue(ref_signals['output_signal'] == expected_outputs)        
        self.assertTrue(dut_signals['output_signal'] == expected_outputs)


class InitialValueVerilogTests(InitialValueTestMixin, unittest.TestCase):

    def cosimulate(self, *args, **kwargs):
        return vivado_verilog_cosimulation(*args, **kwargs)

class InitialValueVHDLTests(InitialValueTestMixin, unittest.TestCase):

    def cosimulate(self, *args, **kwargs):
        return vivado_vhdl_cosimulation(*args, **kwargs)
