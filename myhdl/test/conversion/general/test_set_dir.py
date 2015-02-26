import os

from myhdl import *
from tempfile import mkdtemp
from shutil import rmtree

import myhdl
_version = myhdl.__version__.replace('.','')
_shortversion = _version.replace('dev','')

def simple_dir_model(din, dout, clk):
    """ Simple convertible model """

    @always(clk.posedge)
    def register():
            dout.next = din

    return register
        

def test_toVHDL_set_dir():
    '''In order that a developer can define where in the project 
    hierarchy any generated VHDL files should be placed, it should be 
    possible to set a directory attribute on toVHDL controlling this.
    '''
    
    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))

    try:
        toVHDL.directory = tmp_dir
        toVHDL(simple_dir_model, din, dout, clock)

        assert os.path.exists(os.path.join(tmp_dir, 'simple_dir_model.vhd'))

    finally:
        toVHDL.directory = None        
        rmtree(tmp_dir)

def test_toVHDL_myhdl_package_set_dir():
    '''In order that the MyHDL package files are located in the 
    same place as the generated VHDL files, when the directory attribute of 
    toVHDL is set, this location should be used for the generated MyHDL 
    package files.
    '''
    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))

    try:
        toVHDL.directory = tmp_dir
        toVHDL(simple_dir_model, din, dout, clock)

        assert os.path.exists(
            os.path.join(tmp_dir, "pck_myhdl_%s.vhd" % _shortversion))

    finally:

        toVHDL.directory = None

        rmtree(tmp_dir)

def test_toVerilog_set_dir():
    '''In order that a developer can define where in the project 
    hierarchy any generated Verilog files should be placed, it should be 
    possible to set a directory attribute on toVerilog controlling this.
    '''

    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))

    no_testbench_state = toVerilog.no_testbench
    toVerilog.no_testbench = True

    try:
        toVerilog.directory = tmp_dir
        toVerilog(simple_dir_model, din, dout, clock)

        assert os.path.exists(os.path.join(tmp_dir, 'simple_dir_model.v'))

    finally:
        toVerilog.directory = None
        toVerilog.no_testbench = no_testbench_state
        rmtree(tmp_dir)


def test_toVerilog_testbench_set_dir():
    '''In order that generated Verilog test bench files are located in the 
    same place as the Verilog files, when the directory attribute of 
    toVerilog is set, this location should be used for the generated test
    bench files.
    '''

    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))

    no_testbench_state = toVerilog.no_testbench    
    toVerilog.no_testbench = False

    try:
        toVerilog.directory = tmp_dir
        toVerilog(simple_dir_model, din, dout, clock)

        assert os.path.exists(os.path.join(tmp_dir, 'tb_simple_dir_model.v'))

    finally:

        toVerilog.directory = None
        toVerilog.no_testbench = no_testbench_state

        rmtree(tmp_dir)
