from __future__ import absolute_import
import pytest
import myhdl
from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import verify


@block
def sigAugmAssignUnsupported(z, a):
    @always(a)
    def logic():
        z.next += a
    return logic

def test_SigAugmAssignUnsupported():
    z = Signal(intbv(0)[8:])
    a = Signal(intbv(0)[8:])
    with pytest.raises(ConversionError) as e:
        sigAugmAssignUnsupported(z, a).verify_convert()
    assert e.value.kind == _error.NotSupported


@block
def modbvRange(z, a, b):
    @always(a, b)
    def logic():
        s = modbv(0, min=0, max=35)
        s[:] = a + b
        z.next = s
    return logic

def test_modbvRange():
    z = Signal(intbv(0)[8:])
    a = Signal(intbv(0)[4:])
    b = Signal(intbv(0)[4:])
    with pytest.raises(ConversionError) as e:
        modbvRange(z, a, b).verify_convert()
    assert e.value.kind == _error.ModbvRange

@block
def modbvSigRange(z, a, b):
    @always(a, b)
    def logic():
        z.next = a + b
    return logic

def test_modbvSigRange():
    z = Signal(modbv(0, min=0, max=42))
    a = Signal(intbv(0)[4:])
    b = Signal(intbv(0)[4:])

    with pytest.raises(ConversionError) as e:
        modbvSigRange(z, a, b).verify_convert()
    assert e.value.kind == _error.ModbvRange
