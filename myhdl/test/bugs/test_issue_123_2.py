
import myhdl
from myhdl import Signal, ResetSignal, always
from myhdl.conversion import analyze


"""
This test exposes a hierarchy analysis issue that occures when
a list of generators is returned versus a list-tuple.

    def mod1():
        return gen1
    mods += [mod1()]  # successful

    def mod2():
        return [gen1]
    mods += mod2()    # fails

The above outlines a slight difference in the above examples
fails for an inconsistent hierarchy error in MyHDL 1.0.


Use py.test to run the test

  >> py.test sim=iverilog test_issue_123_1.py

"""

me = 0
port_map = {
     'clock': Signal(bool(0)),
     'x': Signal(bool(0)),
     'y': Signal(bool(0))
}


class Interface:
    def __init__(self):
        self.x = Signal(bool(0))
        self.y = Signal(bool(0))


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


def test_issue_123_2_1():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_2_1'
     myhdl.dump_hierarchy(list_of_interfaces_top_1, **port_map)
     assert analyze(list_of_interfaces_top_1, **port_map) == 0


def test_issue_123_2_2():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_2_2'
     myhdl.dump_hierarchy(list_of_interfaces_top_2, **port_map)
     assert analyze(list_of_interfaces_top_2, **port_map) == 0


if __name__ == '__main__':
    analyze.simulator='iverilog'
    print("-"*80)
    print("Test1")
    print("-"*80)
    test_issue_123_2_1()
    print("-"*80)
    print("Test2")
    print("-"*80)    
    test_issue_123_2_2()
