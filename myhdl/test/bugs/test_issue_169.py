from myhdl import Signal, block, delay, instance

import pytest


class MyTest1:
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


class MyTest2:
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
def mytest_bench():
    inst1 = MyTest1()
    inst2 = MyTest2()
    
    # Two instances are created
    ins1 = inst1.test()
    ins2 = inst2.test()

    return ins1, ins2

#@pytest.mark.xfail
def test_issue_169():
    test_inst = mytest_bench()
    test_inst.verify_convert()

