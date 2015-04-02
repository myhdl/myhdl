from __future__ import absolute_import
from myhdl import *

def bench_SliceSlicedSignal():

	s = Signal(intbv(0)[8:])
	a, b = s(8,4), s(4,0)
	aa, ab = a(4,2), a(2,0)
	ba, bb = b(4,2), b(2,0)

	@instance
	def check():
		for i in range(2**len(s)):
			s.next = i
			yield delay(10)
			assert s[8:6] == aa
			assert s[6:4] == ab
			assert s[4:2] == ba
			assert s[2:0] == bb

	return check

def test_SliceSlicedSignal():
	Simulation(bench_SliceSlicedSignal()).run()


def bench_ConcatConcatedSignal():

	aa = Signal(intbv(0)[2:0])
	ab = Signal(intbv(0)[2:0])
	a = ConcatSignal(aa,ab)

	ba = Signal(intbv(0)[2:0])
	bb = Signal(intbv(0)[2:0])
	b = ConcatSignal(ba,bb)

	s = ConcatSignal(a,b)

	@instance
	def check():
		for iaa in range(2**len(aa)):
			for iab in range(2**len(ab)):
				for iba in range(2**len(ba)):
					for ibb in range(2**len(bb)):
						aa.next = iaa
						ab.next = iab
						ba.next = iba
						bb.next = ibb
						yield delay(10)
 						assert s[8:6] == aa
						assert s[6:4] == ab
						assert s[4:2] == ba
						assert s[2:0] == bb
	return check

def test_ConcatConcatedSignal():
	Simulation(bench_ConcatConcatedSignal()).run()
