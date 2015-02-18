import os

from myhdl import *
from tempfile import mkdtemp
from shutil import rmtree

def simple_dir_model(din, dout, clk):
    """ Simple convertible model """

    @always(clk.posedge)
    def register():
            dout.next = din

    return register
        

def test_toVHDL_set_dir():
    
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


def test_toVerilog_set_dir():
    
    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))
    toVerilog.no_testbench = True

    try:
        toVerilog.directory = tmp_dir
        toVerilog(simple_dir_model, din, dout, clock)

        assert os.path.exists(os.path.join(tmp_dir, 'simple_dir_model.v'))

    finally:
        toVerilog.directory = None
        rmtree(tmp_dir)

def test_toVerilog_testbench_set_dir():
    
    tmp_dir = mkdtemp()

    din = Signal(intbv(0)[5:])
    dout = Signal(intbv(0)[5:])
    clock = Signal(bool(0))

    toVerilog.no_testbench = False

    try:
        toVerilog.directory = tmp_dir
        toVerilog(simple_dir_model, din, dout, clock)

        assert os.path.exists(os.path.join(tmp_dir, 'tb_simple_dir_model.v'))

    finally:
        toVerilog.directory = None        
        rmtree(tmp_dir)
