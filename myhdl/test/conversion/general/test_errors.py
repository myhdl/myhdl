from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error
from myhdl.conversion import verify


def sigAugmAssignUnsupported(z, a):
    @always(a)
    def logic():
        z.next += a
    return logic

def testSigAugmAssignUnsupported():
    z = Signal(intbv(0)[8:])
    a = Signal(intbv(0)[8:])
    try:
        verify(sigAugmAssignUnsupported, z, a)
    except ConversionError, e:
        assert e.kind == _error.NotSupported
    else:
        assert False


