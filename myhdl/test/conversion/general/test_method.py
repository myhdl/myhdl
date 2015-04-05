from __future__ import absolute_import
import sys
from myhdl import *
from myhdl.conversion import verify

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
        self.AConstant = 3

    def method_func(self, clk, srst, x, y):
        
        # limitation for class method conversion, the object attributes
        # can only be used/accessed during elaboration.
        AConstant = int(self.AConstant)
        @always(clk.posedge)
        def hdl():
            if srst:
                y.next = 0
            else:
                y.next = x + (x+1) + AConstant - 3 

        return hdl

class HdlObjAttr(object):
    def __init__(self, clk, srst, x, y):
        self.clk = clk
        self.srst = srst
        self.x = x
        self.y = y
        self.z = Signal(intbv(0, min=y.min, max=y.max))
        self.hobj = HdlObj()
        
    def method_func(self):
        ifx = self.hobj._mfunc(self.x, self.z)
        @always(self.clk.posedge)
        def hdl():
            if self.srst:
                self.y.next = 0
            else:
                self.y.next = self.x + self.z

        return hdl, ifx

def ObjBench(hObj):

    clk = Signal(False)
    srst = Signal(False)
    x = Signal(intbv(0, min=0, max=16))
    y = Signal(intbv(0, min=0, max=16))

    if hObj == HdlObjAttr:
        hdlobj_inst = hObj(clk, srst, x, y)
        hdl_inst = hdlobj_inst.method_func()
    elif hObj == HdlObjAttrSimple:
        hdlobj_inst = hObj()
        hdl_inst = hdlobj_inst.method_func(clk, srst, x, y)
    elif hObj == HdlObj or hObj == HdlObjObj:
        hdlobj_inst = hObj()
        hdl_inst = hdlobj_inst.method_func(clk, srst, x, y)
    else:
        raise StandardError("Incorrect hOjb %s" % (type(hObj), str(hObj)))


    @instance
    def tb_clkgen():
        clk.next = False
        srst.next = False
        yield delay(10)
        srst.next = True
        yield delay(10)
        srst.next = False
        yield delay(10)
        for i in range(1000):
            yield delay(10)
            clk.next = not clk

    xtable = (1,2,3,4,5,6)
    ytable = (3,5,7,9,11,13)

    @instance
    def tb_stimulus():
        for ii in range(30):
            yield clk.posedge
        assert len(xtable) == len(ytable)
        for ii in range(len(xtable)):
            nx = xtable[ii]
            ny = ytable[ii]
            x.next = nx
            yield clk.posedge
            yield clk.posedge
            print("x %d y %d" % (x, y))
            assert x == nx
            assert y == ny
        raise StopSimulation

    return hdl_inst, tb_clkgen, tb_stimulus


def test_hdlobj():
    assert verify(ObjBench, HdlObj) == 0
    
def test_hdlobjobj():
    assert verify(ObjBench, HdlObjObj) == 0

def test_hdlobjattrsimple():
    assert verify(ObjBench, HdlObjAttrSimple) == 0
    
#def test_hdlobjattr():
#    # object attributes currently not supported, these 
#    # tests are for class method conversion only and not 
#    # class attribute conversion.  When (if) class attribute
#    # is supported remove this test.    
#    assert verify(ObjBench, HdlObjAttr) == 1

if __name__ == '__main__':
    Simulation(ObjBench(HdlObj)).run()
    Simulation(ObjBench(HdlObjAttrSimple)).run()
    Simulation(ObjBench(HdlObjAttr)).run()
