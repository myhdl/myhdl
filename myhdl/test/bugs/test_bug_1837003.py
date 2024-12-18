from myhdl import (block, Signal, instances, always_comb)

from myhdl import ConversionError
from myhdl.conversion._misc import _error


@block
def SubFunction_1837003(xout, yout, xin, yin):

    @always_comb
    def comb():
        x = 4
        y = 2
        xout.next = xin
        yout.next = yin

    return instances()

# def Function_1837003(xout,yout,x,y):
#    return SubFunction_1837003(xout,yout,x,y)


x = Signal(bool(0))
y = Signal(bool(0))
xout = Signal(bool(0))
yout = Signal(bool(0))
xin = Signal(bool(0))
yin = Signal(bool(0))


def test_bug_1837003():
    try:
        SubFunction_1837003(xout, yout, x, y).convert(hdl='Verilog')
    except ConversionError as e:
        assert e.kind == _error.ShadowingVar
    else:
        assert False
