from myhdl import (block, Signal, intbv, modbv, always)

from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import verify


@block
def sigAugmAssignUnsupported(z, a):

    @always(a)
    def comb():
        z.next += a

    return comb


def test_SigAugmAssignUnsupported():
    z = Signal(intbv(0)[8:])
    a = Signal(intbv(0)[8:])
    try:
        verify(sigAugmAssignUnsupported(z, a))
    except ConversionError as e:
        assert e.kind == _error.NotSupported
    else:
        assert False


@block
def modbvRange(z, a, b):

    @always(a, b)
    def comb():
        s = modbv(0, min=0, max=35)
        s[:] = a + b
        z.next = s

    return comb


def test_modbvRange():
    z = Signal(intbv(0)[8:])
    a = Signal(intbv(0)[4:])
    b = Signal(intbv(0)[4:])
    try:
        verify(modbvRange(z, a, b))
    except ConversionError as e:
        assert e.kind == _error.ModbvRange
    else:
        assert False


@block
def modbvSigRange(z, a, b):

    @always(a, b)
    def comb():
        z.next = a + b

    return comb


def test_modbvSigRange():
    z = Signal(modbv(0, min=0, max=42))
    a = Signal(intbv(0)[4:])
    b = Signal(intbv(0)[4:])
    try:
        verify(modbvSigRange(z, a, b))
    except ConversionError as e:
        assert e.kind == _error.ModbvRange
    else:
        assert False
