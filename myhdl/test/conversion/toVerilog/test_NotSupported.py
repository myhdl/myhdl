from __future__ import absolute_import
import os
path = os.path
import unittest

from myhdl import *
from myhdl import ConversionError
from myhdl.conversion._misc import _error

class TestNotSupported(unittest.TestCase):

    def check(self, *args):
        try:
            i = toVerilog(*args)
        except ConversionError as e:
            self.assertEqual(e.kind, _error.NotSupported)
        except:
            self.fail()
        else:
            self.fail()

    def nocheck(self, *args):
        i = toVerilog(*args)

    def testAssList(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    [p, q] = 1, 2
            return logic
        self.check(g, z, a)

    def testAssTuple(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    p, q = 1, 2
            return logic
        self.check(g, z, a)

    def testBackquote(self):
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
        self.check(g, z, a)


    def testClass(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    class c:
                        pass
            return logic
        self.check(g, z, a)


    def testDict(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    d = {}
            return logic
        self.check(g, z, a)

    def testDiv(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = z / a
            return logic
        self.check(g, z, a)

    def testExec(self):
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
        self.check(g, z, a)

    def testFrom(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    from os import path
            return logic
        self.check(g, z, a)

    def testFunction(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    def f():
                        pass
            return logic
        self.check(g, z, a)

    def testGlobal(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    global e
            return logic
        self.check(g, z, a)

    def testImport(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    import os
            return logic
        self.check(g, z, a)

    def testLambda(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    lambda: 1
            return logic
        self.check(g, z, a)

    def testListCompIf(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    l = [i for i in range(5) if i > 1]
            return logic
        self.check(g, z, a)

    def testList(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    l = [1, 2, 3]
            return logic
        self.check(g, z, a)

##     def testPower(self):
##         a = Signal(bool())
##         z = Signal(bool())
##         def g(z, a):
##             while 1:
##                 yield a
##                 z.next = 2 ** 8
##         self.check(g, z, a)

##     def testReturn(self):
##         a = Signal(bool())
##         z = Signal(bool())
##         def g(z, a):
##             while 1:
##                 yield a
##                 z.next = 1
##                 return
##         self.check(g, z, a)

    def testTryExcept(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    try:
                        pass
                    except:
                        pass
            return logic
        self.check(g, z, a)

    def testTryFinally(self):
        a = Signal(bool())
        z = Signal(bool())
        def g(z, a):
            @instance
            def logic():
                while 1:
                    yield a
                    z.next = 1
                    try:
                        pass
                    finally:
                        pass
            return logic
        self.check(g, z, a)

    def testChainedCompare(self):
        a, b, c = [Signal(bool()) for i in range(3)]
        z = Signal(bool())
        def g(z, a, b, c):
            @instance
            def logic():
                while 1:
                    yield a, b, c
                    z.next = a <= b < c
            return logic
        self.check(g, z, a, b, c)

##     def testShortcutAnd(self):
##         a, b = [Signal(bool()) for i in range(2)]
##         z = Signal(bool())
##         def g(z, a, b):
##             while 1:
##                 yield a
##                 if a:
##                     pass
##                 else:
##                     z.next = a and b
##         self.check(g, z, a, b)

##     def testShortcutOr(self):
##         a, b, c  = [Signal(bool()) for i in range(3)]
##         z = Signal(bool())
##         def g(z, a, b):
##             while 1:
##                 yield a
##                 if a:
##                     pass
##                 else:
##                     z.next = a < (b or c)
##         self.check(g, z, a, b)

    def testNonBoolArgAnd(self):
        a = Signal(bool())
        b = intbv(0)[2:]
        z = Signal(bool())
        def g(z, a, b):
            @instance
            def logic():
                while 1:
                    yield a
                    if a:
                        pass
                    else:
                        z.next = a and b
            return logic
        self.check(g, z, a, b)

    def testNonBoolArgOr(self):
        a = Signal(bool())
        b = intbv(0)[2:]
        c = Signal(bool())
        z = Signal(bool())
        def g(z, a, b):
            @instance
            def logic():
                while 1:
                    yield a
                    if a:
                        pass
                    else:
                        z.next = a < (b or c)
            return logic
        self.check(g, z, a, b)

    def testExtraArguments(self):
        a, b, c = [Signal(bool()) for i in range(3)]
        c = [1, 2]
        def g(a, *args):
            return a
        def f(a, b, c, *args):
            @instance
            def logic():
                g(a, b)
                yield a
            return logic
        self.check(f, a, b, c)

    def testExtraPositionalArgsInCall(self):
        a, b, c = [Signal(bool()) for i in range(3)]
        c = [1]
        d = {'b':2}
        def h(b):
            return b
        def g(a):
            @instance
            def logic():
                h(*c)
                yield a
            return logic
        def f(a, b, c):
            return g(a)
        x = self.check(f, a, b, c)

    def testExtraNamedArgsInCall(self):
        a, b, c = [Signal(bool()) for i in range(3)]
        c = [1]
        d = {'b':2}
        def h(b):
            return b
        def g(a):
            @instance
            def logic():
                h(**d)
                yield a
            return logic
        def f(a, b, c):
            return g(a)
        x = self.check(f, a, b, c)



class TestMisc(unittest.TestCase):
    def test(self):
        a, b, c = [Signal(bool()) for i in range(3)]
        c = [1]
        d = {'a':2}
        def h(b):
            return b
        def g(a):
            @instance
            def logic():
                h(a)
                yield a
            return logic
        def f(a, b, c):
            return g(a)
        f(a, b, c)
        x = toVerilog(f, a, b, c)




if __name__ == '__main__':
    unittest.main()


