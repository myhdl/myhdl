from __future__ import absolute_import

from unittest import TestCase

from myhdl import fixbv, Signal, block, instance, always_comb, delay, StopSimulation, toVerilog

@block
def fixop1(x, y, z, w):
    @always_comb
    def inst():
        if x + y > z:
            w.next = z - y
        else:
            w.next = y + x * z

    return inst

@block
def fixop2(x, y, z, w):
    @instance
    def inst():
        while 1:
            yield x, y, z
            if x + y > z:
                w.next = z - y
            else:
                w.next = y + x * z

    return inst


class FixbvTest(TestCase):

    @block
    def bench(self, fixop):
        x = Signal(fixbv(0.125, min=-8, max=8, res=2**-5,
                         round_mode='round', overflow_mode='saturate'))
        y = Signal(fixbv(-2.25, min=-8, max=8, res=2**-6,
                         round_mode='round', overflow_mode='saturate'))
        z = Signal(fixbv(1.125, min=-8, max=8, res=2**-7,
                         round_mode='round', overflow_mode='saturate'))
        w = Signal(fixbv(0, min=-8, max=8, res=2**-4,
                         round_mode='round', overflow_mode='saturate'))
        w_v = Signal(fixbv(0, round_mode='round', overflow_mode='saturate')[8, 3, 4])

        fixop_inst = fixop(x, y, z, w).convert(hdl='verilog')
        fixop_v_inst = fixop(x, y, z, w)

        @instance
        def stimulus():
            print(w, w_v)
            yield delay(10)
            print(w, w_v)
            assert w == w_v
            assert float(w) == -2.125

        return stimulus

    def test_fixop1(self):
        sim = self.bench(fixop1)
        sim.run_sim()

    def test_fixop2(self):
        sim = self.bench(fixop2)
        sim.run_sim()

if __name__ == '__main__':
    unittest.main()
