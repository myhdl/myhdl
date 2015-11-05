
import pytest

import myhdl
from myhdl import (Signal, ResetSignal, always_seq, always_comb,
                   always)
from myhdl.conversion import analyze

"""
This test exposes a hierarchy analysis issue that occures when
a list of generators is returned versus a list-tuple.

    def mod1():
        return gen1, gen2, gen3
    mods += [mod1()]  # successful

    def mod2():
        return [gen1, gen2, gen3]
    mods += mod2()    # fails

The error occurs because of the different behavior of list.append
and list.extend.  The list.append code works because it keeps 
the generator object (or the list/tuple of generators) in the 
function it is returned from.  The list.extend will "flatten" the
generator objects from the return function to the calling 
function.

"""

port_map = {
     'clock': Signal(bool(0)),
     'reset': ResetSignal(0, active=0, async=True),
     'w': Signal(bool(0)), 
     'x':Signal(bool(0)), 
     'y': Signal(bool(0)),
     'z': Signal(bool(0)),
}


me = 0
port_map2 = {
     'clock': Signal(bool(0)),
     'x': Signal(bool(0)),
     'y': Signal(bool(0))
}


class Interface:
    def __init__(self):
        self.x = Signal(bool(0))
        self.y = Signal(bool(0))


def mod_tuple(clock, reset, w, x, y, z):
     b = Signal(bool(0))
     @always_seq(clock.posedge, reset=reset)
     def gen1():
          b.next = w and x
     @always_comb
     def gen2():
          z.next = b or y
     return gen1, gen2


def mod_list_1(clock, reset, w, x, y, z):
     b = Signal(bool(0))
     @always_seq(clock.posedge, reset=reset)
     def gen1():
          b.next = w and x
     @always_comb
     def gen2():
          z.next = b or y
     return [gen1, gen2]

     
def mod_with_interface_1(intf):
    global me
    xi = me
    @always(intf.clock.posedge)
    def rtl():
        intf.y.next = (intf.x + xi) & 1
    me += 1
    return rtl


def mod_with_interface_2(intf):
    global me
    xi = me
    @always(intf.clock.posedge)
    def rtl():
        intf.y.next = (intf.x + xi) & 1
    me += 1
    return [rtl]
     

def hier_inconsistent_top_1(clock, reset, w, x, y, z):
     """ This is the expected failing version """
     mod_insts = []
     a, b, c, d = [Signal(bool(0)) for _ in range(4)]

     mod_insts += [mod_tuple(clock, reset, w, x, y, a)]
     mod_insts += [mod_tuple(clock, reset, a, x, y, b)]
     mod_insts += [mod_tuple(clock, reset, b, x, y, c)]

     @always_comb
     def gen1():
          d.next = w and x and y

     @always_comb
     def gen2():
          z.next = a and b and c and d

     mod_insts += [gen1, gen2]

     return mod_insts


def hier_inconsistent_top_2(clock, reset, w, x, y, z):
     """ This is the expected failing version """
     mod_insts = []
     a, b, c, d = [Signal(bool(0)) for _ in range(4)]

     mod_insts += mod_tuple(clock, reset, w, x, y, a)
     mod_insts += mod_list_1(clock, reset, a, x, y, b)
     mod_insts += mod_list_1(clock, reset, b, x, y, c)

     @always_comb
     def gen1():
          d.next = w and x and y

     @always_comb
     def gen2():
          z.next = a and b and c and d

     mod_insts += [gen1, gen2]

     return mod_insts


def list_of_interfaces_top_1(clock, x, y, number_of_modules=7):
    loi = [Interface() for _ in range(number_of_modules)]
    mods = []
    for ii, intf in enumerate(loi):
        if ii == 0:
            intf.x = x
        elif ii == number_of_modules-1:
            intf.y = y
        else:
            intf.x = loi[ii-1].x
        intf.clock = clock
        mods += [mod_with_interface_1(intf)]
    return mods


def list_of_interfaces_top_2(clock, x, y, number_of_modules=7):
    loi = [Interface() for _ in range(number_of_modules)]
    mods = []
    for ii, intf in enumerate(loi):
        if ii == 0:
            intf.x = x
        elif ii == number_of_modules-1:
            intf.y = y
        else:
            intf.x = loi[ii-1].x
        intf.clock = clock
        mods += mod_with_interface_2(intf)
    return mods


def test_extract_1():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_1'
     myhdl.dump_hierarchy(mod_tuple, **port_map)
     assert analyze(mod_tuple, **port_map) == 0


def test_extract_2():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_2'
     myhdl.dump_hierarchy(mod_list_1, **port_map)
     assert analyze(mod_list_1, **port_map) == 0


def test_extract_3():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_3'
     myhdl.dump_hierarchy(hier_inconsistent_top_1, **port_map)
     assert analyze(hier_inconsistent_top_1, **port_map) == 0


def test_extract_4():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_4'
     myhdl.dump_hierarchy(hier_inconsistent_top_2, **port_map)
     with pytest.raises(myhdl.ExtractHierarchyError):
         assert analyze(hier_inconsistent_top_2, **port_map) == 0


@pytest.mark.xfail(analyze.simulator in ('vcom', 'ghdl'),
                   reason="new bug not dealt with yet")         
def test_extract_5():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_5'
     myhdl.dump_hierarchy(list_of_interfaces_top_1, **port_map2)
     assert analyze(list_of_interfaces_top_1, **port_map2) == 0


def test_extract_6():
     myhdl.toVHDL.name = myhdl.toVerilog.name = 'extract_hier_6'
     myhdl.dump_hierarchy(list_of_interfaces_top_2, **port_map2)
     with pytest.raises(myhdl.ExtractHierarchyError):
         assert analyze(list_of_interfaces_top_2, **port_map2) == 0
         

