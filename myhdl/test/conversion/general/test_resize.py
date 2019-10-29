from myhdl import *

import sys

"""Test case #<ISSUE_NUMBER> (hackfin@section5.ch)

- Conversion to VHDL is inconsistent with the MyHDL simulation on sign extension
  of unsigned/signed datatypes. In fact, I'd consider it broken. I had fixed it
  for the time being years ago, now revisiting current releases, I am amazed to
  still see this bug. Why the bug report went to nirvana is a mystery to me...

"""

#               [sign extend]    [unsigned]
t_lmode = enum('LB', 'LH', 'LW', 'LBU', 'LHU')

VERSION = sys.version_info

@block
def resize_vectors(clk, mode, data_out, data_in, IMM):
	"Resize signed and unsigned test case"
	@always_comb
	def worker():
		if mode == t_lmode.LB:
			data_out.next = data_in[8:].signed()
		elif mode == t_lmode.LH:
			data_out.next = data_in[16:].signed()
		elif mode == t_lmode.LBU:
			data_out.next = data_in[8:]
		elif mode == t_lmode.LHU:
			data_out.next = data_in[16:]
		else:
			data_out.next = data_in

	return instances()

@block
def resize_vectors_op(clk, mode, data_out, data_in, IMM):
	"Resize signed and unsigned test case #316"
	@always_comb
	def worker():
		if mode == t_lmode.LB:
			data_out.next = data_in[8:].signed() | IMM
		elif mode == t_lmode.LH:
			data_out.next = data_in[16:].signed() | IMM
		elif mode == t_lmode.LBU:
			data_out.next = data_in[8:] | IMM
		elif mode == t_lmode.LHU:
			data_out.next = data_in[16:] | IMM
		else:
			data_out.next = data_in | IMM


	return instances()
	

@block
def tb_resize_vectors(uut, DATA_IN, DATA_IMM, MODE, DATA_OUT):
	data_in = Signal(modbv()[DATA_IN[1]:])
	data_out, data_check = [ Signal(modbv()[DATA_OUT[1]:]) for i in range(2) ]
	mode = Signal(t_lmode.LW)
	clk = Signal(bool(0))

	inst_uut = uut(clk, mode, data_out, data_in, DATA_IMM)


	@instance
	def stimulus():
		data_in.next = DATA_IN[0]
		data_check.next = DATA_OUT[0]
		mode.next = MODE

		yield delay(10)
		clk.next = not clk
		yield delay(10)
		clk.next = not clk

		if mode == t_lmode.LB:
			print("LB     ")
		elif mode == t_lmode.LBU:
			print("LBU    ")
		elif mode == t_lmode.LH:
			print("LH     ")
		elif mode == t_lmode.LHU:
			print("LHU    ")
		else:
			print("LW     ")

		if data_out == data_check:
			print("PASS")
			print(data_out)
		else:
			print("FAIL")
			print(data_out)
			raise ValueError("resize error, result %x" % data_out)

		# raise StopSimulation()

	return instances()

CHECK_LIST = (
	( resize_vectors,    (0x80, 32),       None,     t_lmode.LB,  (0xffffff80, 32) ),
	( resize_vectors,    (0x80, 32),       None,     t_lmode.LBU, (0x00000080, 32) ),
	( resize_vectors,    (0xbeef, 32),     None,     t_lmode.LH,  (0xffffbeef, 32) ),
	( resize_vectors,    (0xbeef, 32),     None,     t_lmode.LHU, (0x0000beef, 32) ),
	( resize_vectors,    (0x8000beef, 32), None,     t_lmode.LW,  (0x8000beef, 32) ),
	# Result is truncated
	( resize_vectors_op, (0x80, 32),       0x0f0000, t_lmode.LW,  (0x000080, 16) ),
	( resize_vectors_op, (0xdeadbeef, 32), 0x0f0000, t_lmode.LH,  (0xffbeef, 24) ),
	( resize_vectors_op, (0x0000beef, 24), 0x800000, t_lmode.LH,  (0x0fbeef, 20) ),
	# Result is expanded:
	( resize_vectors_op, (0x80, 16),       0x0f0000, t_lmode.LW,  (0x0f0080, 24) ),
	# This is a tricky one, this must NOT sign extend:
	( resize_vectors_op, (0x80, 16),       0x008000, t_lmode.LH,  (0x008080, 24) ),
	# Negative operands:
	( resize_vectors_op, (0x80, 24),       -32,      t_lmode.LW,  (0xffffe0, 24) ),
)

		

def check_resize_vectors(uut, din, imm, m, dout):
	assert tb_resize_vectors(uut, din, imm, m, dout).verify_convert() == 0

def test_resize_vectors():
	for uut, din, imm, m, dout in CHECK_LIST:
		yield check_resize_vectors, uut, din, imm, m, dout

def manual_test():
	"""
This specific case goes wrong for a recent GHDL checkout:
	 
To reproduce manually, run this:
	
	 python test_resize.py && ghdl -i --std=08 tb_resize_vectors.vhd \
	 		pck_myhdl_011.vhd && ghdl -m --std=08 tb_resize_vectors && \
	 	./tb_resize_vectors

	
	Output when converted incorrectly:

> LH     
> FAIL
> 0000BEEF

	Output when converted correctly:

> LH     
> PASS


"""

	uut, din, imm, mode, dout = CHECK_LIST[8]
	tb_resize = tb_resize_vectors(uut, din, imm, mode, dout)
	tb_resize.convert("VHDL")

	return tb_resize

if __name__ == '__main__':

	tb = manual_test()

	traceSignals(tb)
	sim = Simulation(tb)
	sim.run(50000)


