from __future__ import absolute_import
from myhdl import *

WIDTH=4

clk = Signal(bool(0))
x   = Signal(modbv(0)[WIDTH:])
y   = Signal(modbv(0)[WIDTH:])
z   = Signal(modbv(0)[WIDTH:])

@always(delay(5))
def tb_clk_gen():
    clk.next = not clk

@always(clk.posedge)
def inc():
    y.next = x + 1

@always(clk.posedge)
def dec():
    z.next = x - 1

@instance
def tb_stimulus():
    # My logic happens on posedge, so I'll perform all checks on negedge.
    yield clk.negedge
    for x_val in range(-2**WIDTH, 2**WIDTH):
        #print('x_val={} x.next={}'.format(x_val, x_val % 2**WIDTH))
        x.next = x_val % 2**WIDTH
        yield clk.negedge
        assert y==(x_val+1)%2**WIDTH, 'y={} but expected {}'.format(y, (x_val+1)%2**WIDTH)
        assert z==(x_val-1)%2**WIDTH, 'z={} but expected {}'.format(z, (x_val-1)%2**WIDTH)
    print('OK!')
    raise StopSimulation

tb = instances()

def test_bug_44():
    print(instances())
    Simulation(tb).run()

