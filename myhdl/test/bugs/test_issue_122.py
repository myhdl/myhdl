from __future__ import absolute_import
import myhdl
from myhdl import *
from myhdl.conversion import verify 

def issue_122(dout, i):

    d = i*10+1

    @instance
    def write():
        # dout[i].next = int(i)        
        dout[i].next = i        
        yield delay(d)
        print(int(dout[i]))

    if i == 0:
        return write
    else:
        inst = issue_122(dout, i-1)
        return write, inst
                
def tb_issue_122():
    n = 7
    dout = [Signal(intbv(0, min=0, max=n+1)) for i in range(n+1)]
    inst = issue_122(dout, n)
    return inst

def test_issue_122():
    assert verify(tb_issue_122) == 0

