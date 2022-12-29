import myhdl
from myhdl import *

@block
def dut():

    count = Signal(intbv(0, min=0, max=98))

    @instance
    def seq():
        count.next = 50
        for i in range(300):
            yield delay(10)
            print(count)
            if count-1 < 0:
               count.next = 97
            else:
               count.next = count-1
    
    return seq


def test_bug_aj1s():
    assert dut().verify_convert() == 0

