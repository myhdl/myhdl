""" Unit test for Simulation """
from __future__ import generators

import unittest
from unittest import TestCase

import random
from random import randrange
random.seed(1) # random, but deterministic

from myhdl import Simulation, now, delay, StopSimulation, join
from myhdl import Signal, posedge, negedge, intbv
# from myhdl import Signal 

from _simulator import _siglist

class Shared:
    pass

class JoinMix(TestCase):
    """ Test of joins mixed with other clauses """
         
    def test1(self):
        def stimulus():
            a = Signal(0)
            def gen():
                yield join(delay(10), delay(20))
            yield gen(), delay(5)
            self.assertEqual(now(), 5)
            yield a
            self.fail("Incorrect run") # should not get here
        Simulation(stimulus()).run(quiet=1)
        
    def test2(self):
        def stimulus():
            a = Signal(0)
            yield join(delay(10), delay(20)), delay(5)
            self.assertEqual(now(), 5)
            yield a
            self.fail("Incorrect run") # should not get here
        Simulation(stimulus()).run(quiet=1)

    def stimulus(self, a, b, c, d):
        yield delay(5)
        a.next = 1
        yield delay(5)
        a.next = 0
        b.next = 1
        yield delay(5)
        a.next = 1
        b.next = 0
        c.next = 1
        yield delay(5)
        a.next = 0
        b.next = 1
        c.next = 0
        d.next = 1
        
    def test3(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, b, c, d)
            self.assertEqual(now(), 20)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)
        
    def test4(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, b), join(c, d)
            self.assertEqual(now(), 10)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)
        
    def test5(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a), b, join(c, d)
            self.assertEqual(now(), 5)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)
        
    def test6(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, delay(20)), b, join(c, d)
            self.assertEqual(now(), 10)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)

    def test7(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, delay(30)), join(c, d)
            self.assertEqual(now(), 20)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)

    def test8(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, negedge(a))
            self.assertEqual(now(), 10)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)

    def test9(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, negedge(a), posedge(c))
            self.assertEqual(now(), 15)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)

    def test10(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, a)
            self.assertEqual(now(), 5)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)
        
    def test11(self):
        a, b, c, d = [Signal(0) for i in range(4)]
        def response():
            yield join(a, posedge(b), negedge(b), a)
            self.assertEqual(now(), 15)
        Simulation(self.stimulus(a, b, c, d), response()).run(quiet=1)
          

class JoinedGen(TestCase):
    
    """ Basic test of yielding joined concurrent generators """
    
    def bench(self):
        clk = Signal(0)
        sig1 = Signal(0)
        sig2 = Signal(0)
        td = 10

        def gen(s, n):
            for i in range(n-1):
                yield delay(td)
            s.next = 1
            yield delay(td)

        for i in range(10):
            offset = now()
            n0 = randrange(1, 50)
            n1 = randrange(1, 50)
            n2 = randrange(1, 50)
            sig1.next = 0
            sig2.next = 0
            yield join(delay(n0*td), gen(sig1, n1), gen(sig2, n2))
            self.assertEqual(sig1.val, 1)
            self.assertEqual(sig2.val, 1)
            self.assertEqual(now(), offset + td * max(n0, n1, n2))

        raise StopSimulation, "Joined concurrent generator yield"

    def testYieldJoinedGen(self):
        Simulation(self.bench()).run(quiet=1)
        

class SignalUpdateFirst(TestCase):
    
    """ Check that signal updates are done first, as in VHDL """
    
    def bench(self):

        Q = Signal(0, delay=9)
        R = Signal(0, delay=10)
        S = Signal(0, delay=11)

        def process():
            Q.next = 0
            R.next = 0
            S.next = 0
            yield delay(50)
            Q.next = 1
            R.next = 1
            S.next = 1
            yield delay(10)
            self.assertEqual(Q.val, 1) # control
            self.assertEqual(R.val, 1) # actual check
            self.assertEqual(S.val, 0) # control
            yield delay(1)
            self.assertEqual(Q.val, 1) # control
            self.assertEqual(R.val, 1) # control
            self.assertEqual(S.val, 1) # control
            raise StopSimulation, "Signal update test"

        return process()

    def testSignalUpdateFirst(self):
        Simulation(self.bench()).run(quiet=1)
        
        
class YieldZeroDelay(TestCase):
    
    """ Basic test of yielding a zero delay """
    
    def bench(self):
        clk = Signal(0)
        sig1 = Signal(0)
        sig2 = Signal(0)
        td = 10

        def gen(s, n):
            s.next = 0
            for i in range(n):
                yield delay(td)
            s.next = 1

        for i in range(100):
            offset = now()
            n1 = randrange(2, 10)
            n2 = randrange(n1+1, 20) # n2 > n1
            yield delay(0), gen(sig1, n1), gen(sig2, n2)
            self.assertEqual(sig1.val, 0)
            self.assertEqual(sig2.val, 0)
            self.assertEqual(now(), offset + 0)
            yield posedge(sig1)
            self.assertEqual(sig2.val, 0)
            self.assertEqual(now(), offset + n1*td)
            yield posedge(sig2)
            self.assertEqual(now(), offset + n2*td)
        
        raise StopSimulation, "Zero delay yield"

    def testYieldZeroDelay(self):
        Simulation(self.bench()).run(quiet=1)


class YieldConcurrentGen(TestCase):
    
    """ Basic test of yielding concurrent generators """
    
    def bench(self):
        clk = Signal(0)
        sig1 = Signal(0)
        sig2 = Signal(0)
        td = 10

        def gen(s, n):
            s.next = 0
            for i in range(n):
                yield delay(td)
            s.next = 1

        for i in range(100):
            offset = now()
            n1 = randrange(2, 10)
            n2 = randrange(n1+1, 20) # n2 > n1
            yield delay(td), gen(sig1, n1), gen(sig2, n2)
            self.assertEqual(sig1.val, 0)
            self.assertEqual(sig2.val, 0)
            self.assertEqual(now(), offset + td)
            yield posedge(sig1)
            self.assertEqual(sig2.val, 0)
            self.assertEqual(now(), offset + n1*td)
            yield posedge(sig2)
            self.assertEqual(now(), offset + n2*td)

        raise StopSimulation, "Concurrent generator yield"

    def testYieldConcurrentGen(self):
        Simulation(self.bench()).run(quiet=1)

        

class YieldGen(TestCase):
    
    """ Basic test of yielding generators """
    
    def bench(self):

        clk = Signal(0)
        shared = Shared()
        shared.cnt = 0
        shared.i = 0
        expected = []
        nlists = []
        expectedCnt = 0
        for i in range(300):
            l = []
            for j in range(randrange(1, 6)):
                e = randrange(0, 5)
                l.append(e)
                expectedCnt += e
                expected.append(expectedCnt)
            nlists.append(l)                

        def clkGen():
            while 1:
                yield delay(10)
                clk.next = 1
                yield delay(10)
                clk.next = 0

        def task(nlist):
            n = nlist.pop(0)
            for i in range(n):
                yield posedge(clk)
                shared.cnt += 1
            self.assertEqual(shared.cnt, expected[shared.i])
            shared.i += 1
            if nlist:
                yield task(nlist)
                
        def module():
            for nlist in nlists:
                yield task(nlist)
            self.assertEqual(shared.cnt, expected[-1])
            raise StopSimulation, "Generator yield"

        return(module(), clkGen())

    def testYieldGen(self):
        Simulation(self.bench()).run(quiet=1)


class DeltaCycleOrder(TestCase):
    
    """ Check that delta cycle order does not matter """

    def bench(self, function):

        clk = Signal(0)
        a = Signal(0)
        b = Signal(0)
        c = Signal(0)
        d = Signal(0)
        z = Signal(0)
        delta = [Signal(0) for i in range(4)]
        inputs = Signal(intbv(0))
        s = [a, b, c, d]
        vectors = [intbv(j) for i in range(8) for j in range(16)]
        random.shuffle(vectors)
        index = range(4)

        def clkGen():
            while 1:
                yield delay(10)
                clk.next ^= 1

        def deltaGen():
            while 1:
                yield clk
                delta[0].next = clk.val
                yield delta[0]
                for i in range(1, 4):
                    delta[i].next = delta[i-1].val
                    yield delta[i]

        def inGen(i):
            while 1:
                yield posedge(delta[i])
                s[index[i]].next = inputs.val[index[i]]

        def logic():
            while 1:
                yield a, b, c, d
                z.next = function(a.val, b.val, c.val, d.val)

        def stimulus():
            for v in vectors:
                inputs.next = v
                random.shuffle(index)
                yield posedge(clk)
                yield negedge(clk)
                self.assertEqual(z.val, function(v[0], v[1], v[2], v[3]))
            raise StopSimulation, "Delta cycle order"

        inputGen = [inGen(i) for i in range(4)]
        instance = [clkGen(), deltaGen(), logic(), stimulus(), inputGen]
        return instance

    def testAnd(self):
        def andFunction(a, b, c, d):
            return a & b & c & d
        Simulation(self.bench(andFunction)).run(quiet=1)
        
    def testOr(self):
        def orFunction(a, b, c, d):
            return a | b | c | d
        Simulation(self.bench(orFunction)).run(quiet=1)
        
    def testXor(self):
        def xorFunction(a, b, c, d):
            return a ^ b ^ c ^ d
        Simulation(self.bench(xorFunction)).run(quiet=1)

    def testMux(self):
        def muxFunction(a, b, c, d):
            if c:
                return a
            else:
                return b
        Simulation(self.bench(muxFunction)).run(quiet=1)

    def testLogic(self):
        def function(a, b, c, d):
            return not (a & (not b)) | ((not c) & d)
        Simulation(self.bench(function)).run(quiet=1)
    

class DeltaCycleRace(TestCase):
    
    """ Check that delta cycle races are like in VHDL """
    
    def bench(self):
        
        uprange = range(300)
        msig = Signal(uprange[0])
        ssig = [Signal(uprange[-1]) for i in range(2)]
        dsig = [Signal(uprange[0]) for i in range(2)]
        clk = Signal(0)
        deltaClk = Signal(0)
        shared = Shared()
        shared.t = now()
        
        def clkGen():
            for i in uprange[:-1]:
                yield delay(10)
                clk.next = 1
                yield delay(10)
                clk.next = 0
                
        def deltaClkGen():
            while 1:
                yield clk
                deltaClk.next = clk.val
            
        def master():
            i = 0
            while 1:
                yield posedge(clk)
                msig.next = uprange[i+1]
                self.assertEqual(msig.val, uprange[i])
                shared.t = now()
                i += 1
                
        def slave(ssig):
            """ Double-check proper operation """
            i = 0
            while 1:
                yield posedge(clk)
                ssig.next = msig.val
                self.assertEqual(ssig.val, uprange[i-1])
                i += 1

        def deltaSlave(dsig):
            """ Expect delta cycle races """
            i = 0
            while 1:
                yield posedge(deltaClk)
                dsig.next = msig.val
                self.assertEqual(now(), shared.t)
                self.assertEqual(dsig.val, uprange[i])
                i += 1
                
        return (slave(ssig[1]), deltaSlave(dsig[1]),
                master(), clkGen(), deltaClkGen(),
                slave(ssig[0]), deltaSlave(dsig[0]))
    
    
    def testDeltaCycleRace(self):
        """ Check delta cycle races """
        bench = self.bench()
        Simulation(bench).run(quiet=1)


class DelayLine(TestCase):
    
    """ Check that delay lines work properly """

    def bench(self):
        uprange = range(500)
        sig_Z = [Signal(uprange[-i]) for i in range(7)]
        clk = Signal(0)
        
        def clkGen():
            for i in uprange[:-1]:
                yield delay(10)
                clk.next = 1
                yield delay(10)
                clk.next = 0
                
        def delayElement(n, i):
                sig_Z[n].next = sig_Z[n-1].val
                self.assertEqual(sig_Z[n].val, uprange[i-n])
                
        def stage(n):
            i = 0
            while 1:
                yield posedge(clk)
                delayElement(n, i)
                i += 1
                
        def stage012():
            i = 0
            while 1:
                yield posedge(clk)
                delayElement(1, i)
                sig_Z[0].next = uprange[i+1]
                delayElement(2, i)
                i += 1
                
        return [stage(6), stage(4), clkGen(), stage(3), stage012(), stage(5)]
                   
    def testZeroDelay(self):
        """ Zero delay behavior """
        bench = self.bench()
        Simulation(bench).run(quiet=1)



def initSignal(waveform):
    interval, val, sigdelay = waveform[0]
    if sigdelay:
        return Signal(val=val, delay=sigdelay)
    else:
        return Signal(val=val)

def isPosedge(oldval, val):
    return not oldval and val

def isNegedge(oldval, val):
    return oldval and not val

def isEvent(oldval, val):
    return oldval != val

def isEdge(oldval, val):
    return isPosedge(oldval, val) or isNegedge(oldval, val)

def getExpectedTimes(waveform, eventCheck):
    interval, val, sigdelay = waveform[0]
    # print waveform[0]
    expected = []
    time = interval
    oldval = val
    i = 1
    while i < len(waveform):
        interval, val, sigdelay = waveform[i]
        # print waveform[i]
        time += interval
        # check future events within inertial delay interval
        j = i+1
        inctime = 0
        while j < len(waveform) and inctime + waveform[j][0] < sigdelay:
            inctime += waveform[j][0]
            newval = waveform[j][1]
            newsigdelay = waveform[j][2]
            if newval != val: # cancel event
                break
            else: # same vals
                if inctime + newsigdelay < sigdelay:
                    # special case: there is a later event, with same val,
                    # but smaller delay: presumably, this should win,
                    # so cancel the present one
                    break
            j += 1
        else: # if event was not cancelled by a break
            if eventCheck(oldval, val):
                expected.append(time + sigdelay)
                # print expected[-1]
            oldval = val
        i += 1
    # print expected
    return expected


class Waveform(TestCase):
    
    """ Test of all sorts of event response in a waveform """

    waveform = []
    duration = 0
    sigdelay = 0
    for i in range(2000):
        interval = randrange(0, 150)
        val = randrange(0, 4)
        waveform.append((interval, val, sigdelay))
        duration = interval + duration
         
    def stimulus(self):
        for interval, val, sigdelay in self.waveform:
            yield delay(interval)
            self.sig.next = val
            if sigdelay:
                self.sig.delay = sigdelay

    def response(self, clause, expected):
        self.assert_(len(expected) > 100) # we should test something
        i = 0
        while 1:
            yield clause
            self.assertEqual(now(), expected[i])
            i += 1
            
    def setUp(self):
        self.sig = initSignal(self.waveform)

    def run(self, sim):
        sim.run(quiet=1)
                 
    def testPosedge(self):
        """ Posedge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isPosedge)     
        response = self.response(clause=posedge(s), expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())

    def testNegedge(self):
        """ Negedge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isNegedge)     
        response = self.response(clause=negedge(s), expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())

    def testEdge(self):
        """ Edge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isEdge)
        response = self.response(clause=(negedge(s), posedge(s)),
                                 expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())

    def testEvent(self):
        """ Event waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isEvent)     
        # print expected
        response = self.response(clause=s, expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())
            
    def testRedundantEvents(self):
        """ Redundant event waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isEvent)     
        response = self.response(clause=(s,) * 6, expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())
        
    def testRedundantEventAndEdges(self):       
        """ Redundant edge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isEvent)     
        response = self.response(clause=(s, negedge(s), posedge(s)),
                                 expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())
        
    def testRedundantPosedges(self):
        """ Redundant posedge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isPosedge)     
        response = self.response(clause=(posedge(s),) * 3, expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())

    def testRedundantNegedges(self):
        """ Redundant negedge waveform test """
        s = self.sig
        stimulus = self.stimulus()
        expected = getExpectedTimes(self.waveform, isNegedge)     
        response = self.response(clause=(negedge(s),) * 9, expected=expected)
        self.run(Simulation(stimulus, response))
        self.assert_(self.duration <= now())

        
class WaveformSigDelay(Waveform):
    
    """ Repeat waveform tests with a delayed signal """

    waveform = []
    duration = 0
    sigdelay = 0
    for i in range(2000):
        interval = randrange(20, 150)
        val = randrange(0, 4)
        sigdelay = randrange(1, 20)
        waveform.append((interval, val, sigdelay))
        duration += interval
        

class WaveformInertialDelay(Waveform):
    
    """ Repeat waveform tests to check inertial delay """

    waveform = []
    duration = 0
    sigdelay = 0
    for i in range(2000):
        interval = randrange(3, 10)
        val = randrange(0, 3)
        sigdelay = randrange(1, 5)
        waveform.append((interval, val, sigdelay))
        duration += interval

class WaveformInertialDelayStress(Waveform):
    
    """ Repeat waveform tests to stress inertial delay """

    waveform = []
    duration = 0
    sigdelay = 0
    for i in range(2000):
        interval = randrange(1, 3)
        val = randrange(0, 3)
        sigdelay = randrange(1, 3)
        waveform.append((interval, val, sigdelay))
        duration += interval

class SimulationRunMethod(Waveform):
    
    """ Basic test of run method of Simulation object """
    
    def run(self, sim):
        duration = randrange(1, 300)
        while sim.run(duration, quiet=1):
            duration = randrange(1, 300)

      
class TimeZeroEvents(TestCase):

    """ Check events at time 0 """

    def bench(self, sig, next, clause, timeout=1):
        val = sig.val
        def stimulus():
            sig.next = next
            yield delay(10)
        def response():
            yield clause, delay(timeout)
            self.assertEqual(now(), 0)
            self.assertEqual(sig.val, next)
        return [stimulus(), response()]

    def testEvent(self):
        """ Event at time 0 """
        s = Signal(0)
        testBench = self.bench(sig=s, next=1, clause=s)
        Simulation(testBench).run(quiet=1)

    def testPosedge(self):
        """ Posedge at time 0 """
        s = Signal(0)
        testBench = self.bench(sig=s, next=1, clause=posedge(s))
        Simulation(testBench).run(quiet=1)
        
    def testNegedge(self):
        """ Negedge at time 0 """
        s = Signal(1)
        testBench = self.bench(sig=s, next=0, clause=negedge(s))
        Simulation(testBench).run(quiet=1)


        
if __name__ == "__main__":
    unittest.main()
                
