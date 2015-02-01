from __future__ import absolute_import
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

def SubFunction(xout,yout,xin,yin):
    @always_comb
    def logic():
        x = 4
        y = 2
        xout.next = xin
        yout.next = yin
    return instances()


def Function(xout,yout,x,y):
    return SubFunction(xout,yout,x,y)

x = Signal(bool(0))
y = Signal(bool(0))
xout = Signal(bool(0))
yout = Signal(bool(0))
xin = Signal(bool(0))
yin = Signal(bool(0))

def test_bug_1837003():
    try:
        toVerilog(SubFunction,xout,yout,x,y)
    except ConversionError as e:
        assert e.kind == _error.ShadowingVar
    else:
        assert False
