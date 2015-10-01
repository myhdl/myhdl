
import myhdl
from myhdl import Signal, ResetSignal, always_seq, always_comb
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

The above outlines a slight difference in the above examples
fails for an inconsistent hierarchy error in MyHDL 1.0.


Use py.test to run the test

  >> py.test sim=iverilog test_issue_123_1.py

"""

port_map = {
     'clock': Signal(bool(0)),
     'reset': ResetSignal(0, active=0, async=True),
     'w': Signal(bool(0)), 
     'x':Signal(bool(0)), 
     'y': Signal(bool(0)),
     'z': Signal(bool(0)),
}


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


def mod_list_2(clock, reset, w, x, y, z):
     b = Signal(bool(0))
     @always_seq(clock.posedge, reset=reset)
     def gen1():
          b.next = w and x
     @always_comb
     def gen2():
          z.next = b or y
     gen_insts_list = [gen1, gen2]
     return gen_insts_list


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
     mod_insts += mod_list_2(clock, reset, b, x, y, c)

     @always_comb
     def gen1():
          d.next = w and x and y

     @always_comb
     def gen2():
          z.next = a and b and c and d

     mod_insts += [gen1, gen2]

     return mod_insts
     

def test_issue_123_1():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_1_1'
     myhdl.dump_hierarchy(mod_tuple, **port_map)
     assert analyze(mod_tuple, **port_map) == 0


def test_issue_123_2():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_1_2'
     myhdl.dump_hierarchy(mod_list_1, **port_map)
     assert analyze(mod_list_1, **port_map) == 0


def test_issue_123_3():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_1_3'
     myhdl.dump_hierarchy(mod_list_2, **port_map)
     assert analyze(mod_list_2, **port_map) == 0


def test_issue_123_4():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_1_4'
     myhdl.dump_hierarchy(hier_inconsistent_top_1, **port_map)
     assert analyze(hier_inconsistent_top_1, **port_map) == 0


def test_issue_123_5():
     myhdl.toVHDL.name = myhdl.toVerilog = 'issue_123_1_5'
     myhdl.dump_hierarchy(hier_inconsistent_top_2, **port_map)
     assert analyze(hier_inconsistent_top_2, **port_map) == 0


if __name__ == '__main__':
    analyze.simulator='iverilog'
    print('-'*80)
    print("Test 1")
    print('-'*80)
    test_issue_123_1()

    print('-'*80)
    print("Test 2")
    print('-'*80)
    test_issue_123_2()

    print('-'*80)
    print("Test 3")
    print('-'*80)
    test_issue_123_3()

    print('-'*80)
    print("Test 4")
    print('-'*80)
    test_issue_123_4()

    print('-'*80)
    print("Test 5")
    print('-'*80)
    test_issue_123_5()