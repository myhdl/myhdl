import pytest
from myhdl import instance, Signal, toVerilog, ConversionError
from myhdl.conversion._misc import _error
from helpers import raises_kind

def check(*args):
    with raises_kind(ConversionError, _error.NotSupported):
        toVerilog(*args)

def test_Backquote():
    a = Signal(bool())
    z = Signal(bool())
    def g(z, a):
        @instance
        def logic():
            while 1:
                yield a
                z.next = 1
                `a`
        return logic
    check(g, z, a)

def testExec():
    a = Signal(bool())
    z = Signal(bool())
    def g(z, a):
        @instance
        def logic():
            while 1:
                yield a
                z.next = 1
                exec "1 + 2" in globals , locals
        return logic
    check(g, z, a)
