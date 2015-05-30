<<<<<<< HEAD
from __future__ import absolute_import, print_function
=======
from __future__ import absolute_import
>>>>>>> 846f7ad444059d0ca33d36f10adb2214223129f5
from myhdl import *

def constants(v, u, x, y, z, a):

    b = Signal(bool(0))
    c = Signal(bool(1))
    d = Signal(intbv(5)[8:])
    e = Signal(intbv(4, min=-3, max=9))

    @always_comb
    def logic():
        u.next = d
        v.next = e
        x.next = b
        y.next = c
        z.next = a

    return logic


x, y, z, a  = [Signal(bool(0)) for i in range(4)]
u = Signal(intbv(0)[8:])
v = Signal(intbv(0, min=-3, max=9))

def test_constants():
    assert conversion.analyze(constants, v, u, x, y, z, a) == 0 
        
