import os
from myhdl import *

@block
def top(clk, rst, out80, out48, out8):
    counter = Signal(modbv(0)[len(out80):])
    m8  = out8.max - 1
    m48 = out48.max - 1
    m80 = out80.max - 1
    @always(clk.posedge)
    def cnt():
        if rst:
            out8.next  = intbv(0x93)[len(out8):]
            out48.next = intbv(0x3400123400)[len(out48):]
            out80.next = intbv(0x123400001234000066)[len(out80):]
            counter.next = intbv(0x3400004321000066)[len(out80):]
        else:
            out8.next  = counter[8:] & m8
            out48.next = counter[48:] & m48
            out80.next = counter & m80
            counter.next = counter + 1

    return cnt

@block
def tb_top(sim = 'myhdl'):

    clk = Signal(bool(0))
    rst = Signal(bool(0))
    out8 = Signal(intbv(0)[8:])
    out48 = Signal(intbv(55)[48:])
    out80 = Signal(intbv(0)[80:])
    s = {
        'clk':   clk,
        'rst':   rst,
        'out8':  out8,
        'out48': out48,
        'out80': out80
    }

    @always(clk.posedge)
    def dsp():
        print("%g\t %1x   %1x %20x %12x %2x" %
              (now(), clk, rst, out80, out48, out8))

    @instance
    def stim():
        print("time\tclk rst %20s %12s %s" % ('out80', 'out48', 'out8'))
        yield delay(20)
        rst.next = 1
        yield delay(10)
        rst.next = 0
        yield delay(80)
        rst.next = 1
        yield delay(10)
        rst.next = 0
        yield delay(50)
        print("%g\t %1x   %1x %20x %12x %2x" %
              (now(), clk, rst, out80, out48, out8))
        assert out8 == 0x6a
        assert out48 == 0x432100006a
        assert out80 == 0x340000432100006a
        raise StopSimulation

    @always(delay(5))
    def ck():
        clk.next = not clk

    if sim == 'myhdl':
        print("myhdl")
        dut = top(clk, rst, out80, out48, out8)
        dut.convert(hdl='Verilog')
    elif sim == 'icarus':
        print("icarus")
        cmd = 'iverilog -o top top.v tb_top.v'
        os.system(cmd)
        dut = Cosimulation('vvp -m ../../icarus/myhdl_11.0-devel.vpi top', **s)
        print(dut, dir(dut))
    elif sim == 'verilator_vrl':
        print("verilator verilog")
        # dut = Verilation(top_verilog_file='t.v', trace='t.vcd', **s)
        dut = Verilation(top_verilog_file='top.v', **s)
    else:
        print("verilator shared library")
        # dut = Verilation(sofile='obj_dir/Vtop', trace=False, **s)
        dut = Verilation(sofile='obj_dir/Vtop', **s)
        print(dut, dir(dut))

    return dut, stim, ck, dsp


if __name__ == "__main__":

    from pprint import pprint

    tb = tb_top()
    # pprint(dir(tb))
    # pprint(tb.sigdict)
    tb.config_sim(trace=True)
    tb.run_sim()

    ntb = tb_top(sim='icarus')
    ntb.run_sim()

    ntb = tb_top(sim='verilator_vrl')
    ntb.run_sim()

    ntb = tb_top(sim='verilator_shared')
    ntb.run_sim()

    # pprint(tb.sigdict)
