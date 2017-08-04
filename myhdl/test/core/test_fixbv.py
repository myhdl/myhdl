from __future__ import division

import math
from random import randint

import pytest

import myhdl
from myhdl import *

from myhdl import fixbv
from myhdl._fixbv import FixedPointFormat as fpf

def test_fpf_inst():
    ewl,eiwl,efwl = (8,4,3)
    W1 = fpf(8,4,3)
    W2 = fpf(8,4)
    W3 = fpf(wl=8,iwl=4,fwl=3)
    W4 = fpf(*(8,4,3,))

    for ww in (W1,W2,W3,W4):
        wl,iwl,fwl = ww[:]
        assert wl == ewl
        assert iwl == eiwl
        assert fwl == efwl

def test_fpf_add():
    W1 = fpf(8,4)
    W2 = fpf(8,4)
    Wa = W1+W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 5, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 3, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 9, '%s+%s==%s'  % (W1,W2,Wa)

    W1 = fpf(8,4)  # W8.4.3
    W2 = fpf(8,3)  # W8.3.4
    Wa = W1+W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 5, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 4, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 10, '%s+%s==%s'  % (W1,W2,Wa)
    
    W1 = fpf(16,0)  # W16.0.15
    W2 = fpf(16,0)  # W16.0.15
    Wa = W1+W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 1, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 15, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 17, '%s+%s==%s'  % (W1,W2,Wa)

    W1 = fpf(16,1)  # W16.1.14
    W2 = fpf(16,3)  # W16.3.12
    Wa = W1+W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 4, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 14, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 19, '%s+%s==%s'  % (W1,W2,Wa)

    # negative integer widths, fwl larger than the iwl
    # wl(4) = iwl(-4) + fwl + 1
    # fwl = wl(4) - iwl(-4) -1 
    # fwl = 7
    # when adding the total word-length (wl) should increase
    # the number of fractions should increase (until iwl >= 0)
    # and the iwl should increase.
    W1 = fpf(4,-4)
    W2 = fpf(4,-4)
    Wa = W1+W2
    wl,iwl,fwl = Wa[:]
    assert iwl == -3, '%s+%s==%s'  % (W1,W2,afmt)
    assert fwl == 7, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 5, '%s+%s==%s'  % (W1,W2,Wa)

    # The following test case is for fixbv addition. Each
    # add operation would assume the worst case, that is,
    # each addition would cause an overflow. So that the
    # result always adds one more extra integer bit during
    # addition.
    # However, if several fixbv instances add together, the
    # result might be huge and odd if the order of
    # addition changes. In this case, fxsum would be
    # recommended for optimal results.
    W1_iwl = randint(3, 16)
    W2_iwl = randint(3, 16)
    W3_iwl = randint(3, 8)
    W4_iwl = randint(3, 8)
    Wa_iwl = max(W1_iwl, W2_iwl) + 1
    Wa_iwl = max(Wa_iwl, W3_iwl) + 1
    Wa_iwl = max(Wa_iwl, W4_iwl) + 1

    W1 = fpf(16, W1_iwl)
    W2 = fpf(16, W2_iwl)
    W3 = fpf(8, W3_iwl)
    W4 = fpf(8, W4_iwl)
    Wa = W1+W2+W3+W4
    wl, iwl, fwl = Wa[:]

    assert iwl == Wa_iwl, '%s+%s+%s+%s==%s'  % (W1, W2, W3, W4, Wa)

    # cross-over points when negative iwl becomes
    # positive and vise-versa
    W1 = fpf(8, -3)
    W2 = fpf(8, -4)
    niwl = -2
    for ii in range(6):
        W1 = W1 + W2
        assert W1._iwl == niwl
        niwl += 1

    # negative fraction widths
    W1 = fpf(4, 8)
    assert W1._fwl == -5

    # cross-over points when negative fwl becomes
    # positive and vise-versa
    W1 = fpf(4, 8)
    W2 = fpf(10, 8, 1)
    nfwl = -5
    for ii in range(6):
        W1 = W1 * W2
        nfwl += 1
        assert W1._fwl == nfwl


def test_fpf_sub():
    # some basic adds
    W1 = fpf(8,4)  # W8.4.3
    W2 = fpf(8,4)  # W8.4.3
    Wa = W1-W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 5, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 3, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 9, '%s+%s==%s'  % (W1,W2,Wa)

    W1 = fpf(8,4)  # W8.4.3
    W2 = fpf(8,3)  # W8.3.4
    Wa = W1-W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 5, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 4, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 10, '%s+%s==%s'  % (W1,W2,Wa)

    W1 = fpf(16,0)  # W16.0.15
    W2 = fpf(16,0)  # W16.0.15
    Wa = W1-W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 1, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 15, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 17, '%s+%s==%s'  % (W1,W2,Wa)    

def test_fpf_mul():
    W1 = fpf(8,4)  # W8.4.3
    W2 = fpf(8,4)  # W8.4.3
    Wa = W1*W2
    wl,iwl,fwl = Wa[:]
    assert iwl == 9, '%s+%s==%s'  % (W1,W2,Wa)
    assert fwl == 6, '%s+%s==%s'  % (W1,W2,Wa)
    assert wl == 16, '%s+%s==%s'  % (W1,W2,Wa)

    # @todo: negative iwl and fwl

def test_basic():
    # test all exact single bit values for (16,0,15)
    for f in range(1,16):
        x = fixbv(2**-f)[16,0,15]
        y = fixbv(-2**-f)[16,0,15]

        assert float(x) == 2**-f, \
               "%f != %f, %04x != %04x" % (2.**-f, float(x),
                                           x,
                                           0x8000 >> f)
        
        assert bin(x._val,16) == bin(0x8000 >> f, 16), \
               "%s != %s for f == %d" % (bin(x._val, 16),
                                         bin(0x8000 >> f, 16), f)
        
        assert float(y) == -2**-f
        assert bin(y._val,16) == bin(-0x8000 >> f, 16), \
               "%s" % (bin(y._val, 16))


         # Test all exact single bit values for W128.0
    for f in range(1,128):
        x = fixbv(2**-f,  min=-1, max=1, res=2**-127)
        y = fixbv(-2**-f, min=-1, max=1, res=2**-127)
        assert float(x) == 2**-f
        assert bin(x,128) == bin(0x80000000000000000000000000000000 >> f, 128)
        assert float(y) == -2**-f
        assert bin(y,128) == bin(-0x80000000000000000000000000000000 >> f, 128)

    assert x > y
    assert y < x
    assert min(x,y) == min(y,x) == y
    assert max(x,y) == max(y,x) == x
    assert x != y

    x = fixbv(3.14159)[18,3]
    y = fixbv(-1.4142 - 1.161802 - 2.71828)[18,3]

    assert x != y
    #assert --x == x
    assert abs(y) > abs(x)
    assert abs(x) < abs(y)
    assert x == x and y == y

    # Create a (8,3) fixed-point object value == 2.5
    x = fixbv(2.5, min=-8, max=8, res=1./32)
    assert float(x) == 2.5
    assert x._val == 0x50

def test_round_overflow():
    # round mode: round
    x = fixbv(10.1875, min=-16, max=16, res=2**-5,
              round_mode='round', overflow_mode='ring')
    y = fixbv(-3.14, min=-16, max=16, res=2**-6,
              round_mode='round', overflow_mode='ring')
    z = fixbv(-2.125, min=-16, max=16, res=2**-6,
              round_mode='round', overflow_mode='ring')
    w = fixbv(0, min=-16, max=16, res=2**-2,
              round_mode='round', overflow_mode='ring')
    w[:] = x
    assert float(w) == 10.25
    w[:] = y
    assert float(w) == -3.25
    w[:] = z
    assert float(w) == -2

    # round mode: nearest
    x = fixbv(10.625, min=-16, max=16, res=2**-5,
              round_mode='nearest', overflow_mode='ring')
    y = fixbv(-3.14, min=-16, max=16, res=2**-6,
              round_mode='nearest', overflow_mode='ring')
    z = fixbv(-2.125, min=-16, max=16, res=2**-6,
              round_mode='nearest', overflow_mode='ring')
    w = fixbv(0, min=-16, max=16, res=2**-2,
              round_mode='nearest', overflow_mode='ring')
    w[:] = x
    assert float(w) == 10.75
    w[:] = y
    assert float(w) == -3.25
    w[:] = z
    assert float(w) == -2.25

    # round mode: floor
    x = fixbv(10.625, min=-16, max=16, res=2**-5,
              round_mode='floor', overflow_mode='ring')
    y = fixbv(-3.14, min=-16, max=16, res=2**-6,
              round_mode='floor', overflow_mode='ring')
    z = fixbv(-2.125, min=-16, max=16, res=2**-6,
              round_mode='floor', overflow_mode='ring')
    w = fixbv(0, min=-16, max=16, res=2**-2,
              round_mode='floor', overflow_mode='ring')
    w[:] = x
    assert float(w) == 10.5
    w[:] = y
    assert float(w) == -3.25
    w[:] = z
    assert float(w) == -2.25

    # overflow mode: ring
    x = fixbv(10.1875, min=-16, max=16, res=2**-5,
              round_mode='round', overflow_mode='ring')
    y = fixbv(-2., min=-16, max=16, res=2**-6,
              round_mode='round', overflow_mode='ring')
    z = fixbv(-6.125, min=-16, max=16, res=2**-6,
              round_mode='round', overflow_mode='ring')
    w = fixbv(0, min=-4, max=4, res=2**-8,
              round_mode='round', overflow_mode='ring')
    w[:] = x
    assert float(w) == 2.1875
    w[:] = y
    assert float(w) == -2.
    w[:] = z
    assert float(w) == 1.875

    # overflow mode: saturate
    x = fixbv(10.1875, min=-16, max=16, res=2**-5,
              round_mode='saturate', overflow_mode='ring')
    y = fixbv(-2., min=-16, max=16, res=2**-6,
              round_mode='saturate', overflow_mode='ring')
    z = fixbv(-6.125, min=-16, max=16, res=2**-6,
              round_mode='saturate', overflow_mode='ring')
    w = fixbv(0, min=-4, max=4, res=2**-8,
              round_mode='saturate', overflow_mode='ring')
    w[:] = x
    assert float(w) == 4 - 2**-8
    w[:] = y
    assert float(w) == -2.
    w[:] = z
    assert float(w) == -4

def m_round_overflow(x, y):

    @always_comb
    def rtl():
        y.next = x

    return rtl

def test_module_round_overflow():
    x = Signal(fixbv(10.1875, min=-16, max=16, res=2**-5,
                     round_mode='round', overflow_mode='ring'))
    y = Signal(fixbv(0, min=-8, max=8, res=2**-2,
                     round_mode='round', overflow_mode='ring'))

    def _test():
        tbdut = m_round_overflow(x, y)

        @instance
        def tbstim():
            print(x, y)
            yield delay(10)
            print(x, y)
            assert float(y) == -5.75

        return tbdut, tbstim

    Simulation(_test()).run()

def test_math():
    x = fixbv(0.5)[16,0]  
    y = fixbv(0.25)[16,0]
    z = fixbv(0)[16,0]
    #print(x, y, z)
    #w = x + y
    #print(w, type(w))
    z[:] = x + y
    print(z, type(z), x+y)
    assert float(z) == 0.75

    x = fixbv(3.5,   min=-8, max=8, res=2**-5)  
    y = fixbv(-5.25, min=-8, max=8, res=2**-5)
    iW = x._W + y._W
    print(iW)
    z = fixbv(0)[iW[:]]
    z[:] = x + y
    assert float(z) == -1.75

    z[:] = y - x
    assert float(z) == -8.75
    z[:] = x - y
    assert float(z) == 8.75


    x = fixbv(3.141592)[19,4]
    y = fixbv(1.618033)[19,4]
    print(float(x), int(x), repr(x))
    print(float(y), int(y), repr(y))

    iW = x._W * y._W
    print(iW)
    z = fixbv(0)[iW[:]]
    wl,iwl,fwl = z._W[:]
    print(repr(z), z._max, z._min, z._nrbits, "iwl, fwl", iwl, fwl)
    
    z[:] = x * y
    print(repr(x), repr(y))
    print(float(z), int(z), repr(z))
    assert float(z) > 5.

    x = fixbv(3.5, min=-8, max=8, res=2**-5)  
    z = fixbv(0)[(x*x).format]
    print(x, z)
    z[:] = x * x
    assert float(z) == 12.25
    z[:] = x**2
    assert float(z) == 12.25

    z = fixbv(0)[(x*x*x).format]
    z[:] = x * x * x
    assert float(z) == 42.875
    z[:] = x**3
    assert float(z) == 42.875
    
    # Point alignment
    x = fixbv(2.25, min=-4, max=4, res=2**-5)
    y = fixbv(1.5, min=-2, max=2, res=2**-8)
    z = fixbv(0)[12, 4, 7]
    z[:] = x + y
    assert float(z) == 3.75
    z[:] = x - y
    assert float(z) == 0.75
    z[:] = x * y
    assert float(z) == 3.375

    x = fixbv(9.5, min=-16, max=16, res=0.25)
    y = fixbv(-3.25, min=-4, max=4, res=2**-4)
    z = fixbv(0)[11, 6, 4]
    z[:] = x + y
    assert float(z) == 6.25
    z[:] = x - y
    assert float(z) == 12.75
    z[:] = y - x
    assert float(z) == -12.75
    z[:] = x * y
    assert float(z) == -30.875

def m_add(x, y, z):

    @always_comb
    def rtl():
        z.next = x + y

    return rtl

def test_module_add():
    x = Signal(fixbv(3.14159, min=-8, max=8, res=1e-5))
    y = Signal(fixbv(3.14159, min=-8, max=8, res=1e-5))
    z = Signal(fixbv(0, min=-8, max=8, res=1e-5))

    def _test():
        tbdut = m_add(x, y, z)

        @instance
        def tbstim():
            print(x,y,z)
            yield delay(10)
            print(x,y,z)            
            assert float(z) > 6
            assert float(z) < 7
            err = abs(2*math.pi - float(z))
            # @todo: need to quantify what the expected error is
            assert err < 1e-4

        return tbdut, tbstim

    Simulation(_test()).run()

def m_align(x, y, z):
    
    @always_comb
    def rtl():
        z.next = y - x * y + x

    return rtl

def test_module_align():
    x = Signal(fixbv(0.125, min=-32, max=32, res=1/2**8))
    y = Signal(fixbv(0.25, min=-128, max=128, res=1/2**32))
    z = Signal(fixbv(0, min=-16, max=16, res=1/2**16))

    def _test():
        tbdut = m_align(x, y, z)

        @instance
        def tbstim():
            print(x,y,z)
            yield delay(10)
            print(x,y,z)
            

        return tbdut, tbstim

    Simulation(_test()).run()

def m_align_intbv(x, y, z):
    
    @always_comb
    def rtl():
        z.next = y._val + x

    return rtl

def test_module_align_intbv():
    x = Signal(intbv(2, max=32))
    y = Signal(intbv(4, max=128))
    z = Signal(intbv(0, max=16))

    def _test():
        tbdut = m_align_intbv(x, y, z)

        @instance
        def tbstim():
            print(x,y,z)
            yield delay(10)
            print(x,y,z)
            assert int(z) == 6
            

        return tbdut, tbstim

    Simulation(_test()).run()

def m_more(w, x, y, z):
    
    @always_comb
    def rtl():
        if (x + y) > w:
            z.next = x + y - w
        else:
            z.next = (x * w**2) - y**2

    return rtl

def test_module_more():
    w = Signal(fixbv(0.5, min=-128, max=128, res=1/2**32))
    x = Signal(fixbv(0.125, min=-128, max=128, res=1/2**32))
    y = Signal(fixbv(0.125, min=-128, max=128, res=1/2**32))
    z = Signal(fixbv(0, min=-128, max=128, res=1/2**32))

    def _test():
        tbdut = m_more(w, x, y, z)

        @instance
        def tbstim():
            print(w,x,y,z)
            yield delay(10)
            print(w,x,y,z)
            

        return tbdut, tbstim

    Simulation(_test()).run()


def test_equalities():
    x = fixbv(3.14159, min=-8, max=8, res=1e-5)
    y = fixbv(3.14159, min=-8, max=8, res=1e-5)
    z = fixbv(0, min=-8, max=8, res=1e-5)
    w = fixbv(0, min=-16, max=16, res=2**-16)
    u = fixbv(-2.7183, min=-8, max=8, res=1e-5)
    v = fixbv(-2.7183, min=-16, max=16, res=1e-7)

    assert x == y
    assert x >= y
    assert y <= x
    assert z < x
    assert x > z
    assert x != z
    assert x > w
    assert y >= w
    assert z == w
    assert z >= w
    assert z <= w
    assert x > u
    assert u <= y
    assert w >= v
    assert v < x
    # with pytest.raises(AssertionError) as excinfo:
    #     if x == w:
    #         print("nope, this shouldn't work")


    # @todo: now this is an issue, when intbv is in a Signal and 
    #    pass the operators down it will be intbv == Signal
    x = Signal(fixbv(3.14159, min=-8, max=8, res=1e-5))
    y = Signal(fixbv(3.14159, min=-8, max=8, res=1e-5))
    z = Signal(fixbv(0, min=-8, max=8, res=1e-5))
    w = Signal(fixbv(0, min=-16, max=16, res=2**-16))
    u = Signal(fixbv(-2.7183, min=-8, max=8, res=1e-5))
    v = Signal(fixbv(-2.7183, min=-16, max=16, res=1e-7))

    # these tests currrently fail, need to usderstand why
    assert x == y
    assert x >= y
    assert y <= x
    assert z < x
    assert x > z
    assert x != z
    assert x > w
    assert y >= w
    assert z == w
    assert z >= w
    assert z <= w
    assert x > u
    assert u <= y
    assert w >= v
    assert v < x
    # none of the following should work because 'x' and 'w' are
    # different types.  They need to be the same widths before 
    # the comparisons.
    #
    # I added the comparison for different widths. - qrqiuren
    # with pytest.raises(AssertionError) as excinfo:
    #     if x == w: print("nope, this shoudln't work")
    # with pytest.raises(AssertionError) as excinfo:
    #     if x < w: print("nope, this shoudln't work")
    # with pytest.raises(AssertionError) as excinfo:
    #     if w > x: print("nope, this shoudln't work")
    # with pytest.raises(AssertionError) as excinfo:
    #     if x <= w: print("nope, this shoudln't work")
    # with pytest.raises(AssertionError) as excinfo:
    #     if w >= x: print("nope, this shoudln't work")
    # with pytest.raises(AssertionError) as excinfo:
    #     if x != w: print("nope, this shoudln't work")
    
def test_int_frac():
    x = fixbv(3.75, min=-4, max=4, res=0.125)
    print(bin(x._val))
    assert x.int() == 3
    assert x.frac() == 6

    x = fixbv(-4.625, min=-8, max=8, res=0.125)
    print(bin(x._val))
    assert x.int() == -5
    assert x.frac() == 3
    
if __name__ == '__main__':
    #test_fpf_add()
    #test_basic()
    test_math()
    #test_equalities()
    test_module_add()
    test_module_more()


    
