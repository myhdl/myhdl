import os
path = os.path
import unittest

from myhdl import *
from myhdl._toVerilog import ToVerilogError

class TestNotSupported(unittest.TestCase):
    
    def check(self, *args):
        try:
            i = toVerilog(*args)
        except ToVerilogError:
            pass
        except:
            self.fail()
        else:
            self.fail()

    def nocheck(self, *args):
        i = toVerilog(*args)

    def testAssAttr(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.net = 1
        self.check(g, z, a)

    def testAssList(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                [p, q] = 1, 2
        self.check(g, z, a)
            
    def testAssTuple(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                p, q = 1, 2
        self.check(g, z, a)

    def testBackquote(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                `a`
        self.check(g, z, a)
            
    def testBackquote(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                `a`
        self.check(g, z, a)

    def testBreak(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                break
        self.check(g, z, a)
        
    def testClass(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                class c:
                    pass
        self.check(g, z, a)

    def testContinue(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                continue
        self.check(g, z, a)
        
    def testDict(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                d = {}
        self.check(g, z, a)

    def testDiv(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = z / a
        self.check(g, z, a)

    def testExec(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                exec "1 + 2"
        self.check(g, z, a)
        
    def testFrom(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                from os import path
        self.check(g, z, a)

    def testFunction(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                def f():
                    pass
        self.check(g, z, a)

    def testGlobal(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                global e
        self.check(g, z, a)

    def testImport(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                import os
        self.check(g, z, a)

    def testLambda(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                lambda: 1
        self.check(g, z, a)

    def testListComp(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                l = [i for i in range(5) if i > 1]
        self.check(g, z, a)

    def testList(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                l = [1, 2, 3]
        self.check(g, z, a)

    def testPower(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 2 ** 8
        self.check(g, z, a)

    def testReturn(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                return
        self.check(g, z, a)
        
    def testTryExcept(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                try:
                    pass
                except:
                    pass
        self.check(g, z, a)

    def testTryFinally(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = 1
                try:
                    pass
                finally:
                    pass
        self.check(g, z, a)

    def testUnaryAdd(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = +a
        self.check(g, z, a)

    def testUnarySub(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            while 1:
                yield a
                z.next = -a
                return
        self.check(g, z, a)
            

if __name__ == '__main__':
    unittest.main()
    

