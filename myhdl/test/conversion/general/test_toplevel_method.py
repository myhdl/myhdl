from __future__ import absolute_import
import sys
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import analyze

class HdlObj(object):
    def __init__(self):
        pass

    def method_func(self, clk, srst, x, y):
        z = Signal(intbv(0, min=y.min, max=y.max))
        ifx = self._mfunc(x, z)
        @always(clk.posedge)
        def hdl():
            if srst:
                y.next = 0
            else:
                y.next = x + z  # x + (x+1)

        return hdl, ifx

    def _mfunc(self, x, y):
        @always_comb
        def _hdl():
            y.next = x + 1
        return _hdl

def _func(x,y):
    @always_comb
    def _hdl():
        y.next = x + 1
    return _hdl

class HdlObjObj(object):
    def __init__(self):
        pass
    
    def method_func(self, clk, srst, x, y):
        z1 = Signal(intbv(0, min=y.min, max=y.max))
        z2 = Signal(intbv(0, min=y.min, max=y.max))
        hobj = HdlObj()
        ifx1 = hobj._mfunc(x, z1)
        ifx2 = _func(x, z2)
        
        @always(clk.posedge)
        def hdl():
            if srst:
                y.next = 0
            else:
                y.next = x + z1 + (z1 - z2)

        return hdl, ifx1, ifx2    

class HdlObjAttrSimple(object):
    def __init__(self):
        self.Constant = 3

    def method_func(self, clk, srst, x, y):
        
        # limitation for class method conversion, the object attributes
        # can only be used/accessed during elaboration.
        Constant = int(self.Constant)
        @always(clk.posedge)
        def hdl():
            if srst:
                y.next = 0
            else:
                y.next = x + (x+1) + Constant - 3 

        return hdl


class HdlObjNotSelf(object):
    def __init__(this):
        pass

    def method_func(this, clk, srst, x, y):

        @always(clk.posedge)
        def hdl():
            if srst:
                y.next = 0
            else:
                y.next = x + 1

        return hdl


def test_hdlobj():
    clk = Signal(False)
    srst = Signal(False)
    x = Signal(intbv(0, min=0, max=16))
    y = Signal(intbv(0, min=0, max=16))
    hdlobj_inst = HdlObj()
    analyze(hdlobj_inst.method_func, clk, srst, x, y)

def test_hdlobjobj():
    clk = Signal(False)
    srst = Signal(False)
    x = Signal(intbv(0, min=0, max=16))
    y = Signal(intbv(0, min=0, max=16))
    hdlobj_inst = HdlObjObj()
    analyze(hdlobj_inst.method_func, clk, srst, x, y)

def test_hdlobjattrsimple():
    clk = Signal(False)
    srst = Signal(False)
    x = Signal(intbv(0, min=0, max=16))
    y = Signal(intbv(0, min=0, max=16))
    hdlobj_inst = HdlObjAttrSimple()
    analyze(hdlobj_inst.method_func, clk, x, srst, y)


def test_hdlobjnotself():
    clk = Signal(False)
    srst = Signal(False)
    x = Signal(intbv(0, min=0, max=16))
    y = Signal(intbv(0, min=0, max=16))
    hdlobj_inst = HdlObjNotSelf()
    try:
        analyze(hdlobj_inst.method_func, clk, x, srst, y)
    except ConversionError as e:
        assert e.kind == _error.NotSupported
    else:
        assert False



