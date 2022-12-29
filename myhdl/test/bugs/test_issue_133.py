import myhdl
from myhdl import *

@block
def issue_133():
    z = Signal(False)
    large_signal = Signal(intbv(123456789123456, min=0, max=2**256))
    @instance
    def check():
        z.next = large_signal[10]
        yield delay(10)
        print (large_signal[31:])
        print (large_signal[62:31])
        print (large_signal[93:62])

    return check 

def test_issue_133():
    issue_133().verify_convert() == 0
