from myhdl import Signal, block, delay, instance

import pytest


class Test1:
    def __init__(self):
        self.clock = Signal(bool(0))

    @block
    def test(self):
    
        @instance
        def func():
            i = 0
            while i <= 100:
                yield delay(10)
                self.clock.next = not self.clock
                i = i + 1

        return func


class Test2:
    def __init__(self):
        self.clock = Signal(bool(1))

    @block
    def test(self):
    
        @instance
        def func():
            i = 0
            while i <= 100:
                yield delay(10)
                self.clock.next = not self.clock
                i = i + 1

        return func


@block
def test_bench():
    inst1 = Test1()
    inst2 = Test2()
    
    # Two instances are created
    ins1 = inst1.test()
    ins2 = inst2.test()

    return ins1, ins2

@pytest.mark.xfail
def test_issue_169():
    test_inst = test_bench()
    assert test_inst.verify_convert() == True
    
if __name__ == '__main__':
    test_issue_169()

