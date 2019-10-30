from myhdl import *
from myhdl import ConversionError
import sys

"""Test case #<ISSUE_NUMBER> (hackfin@section5.ch)

- Conversion to VHDL is inconsistent with the MyHDL simulation on sign extension
  of unsigned/signed datatypes. 

  There are more special scenarios where the test cases fail. Some of them are fixed,
  some will raise a ConversionError for now. The rule is: Better fail early
  (than producing wrong results turning up during verification)

  See CHECK_LIST for the table of currently executed tests

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
def resize_vectors_op_sane(clk, mode, data_out, data_in, IMM):
	"""Sane way to avoid warnings during VHDL conversion
It is mandatory to define this as constant first, if written verbosely
in the statements below, invalid VHDL will be generated.
"""
	const_imm8 = IMM & 0xff
	const_imm16 = IMM & 0xffff

	@always_comb
	def worker():
		if mode == t_lmode.LB:
			data_out.next = data_in[8:].signed() | const_imm8
		elif mode == t_lmode.LH:
			data_out.next = data_in[16:].signed() | const_imm16
		elif mode == t_lmode.LBU:
			data_out.next = data_in[8:] | const_imm8
		elif mode == t_lmode.LHU:
			data_out.next = data_in[16:] | const_imm16
		else:
			data_out.next = data_in | IMM


	return instances()

@block
def resize_single(clk, mode, data_out, data_in, IMM):
	"""Single resize with immediate constant
"""
	@always_comb
	def worker():
		data_out.next = data_in | IMM

	return instances()

@block
def resize_vectors_add(clk, mode, data_out, data_in, data_add):
	"Resize signed and unsigned test case #316"
	a, b = [ Signal(intbv(0, min=data_add.min, max=data_add.max)) for i in range(2) ]
	@always_comb
	def calc():
		a.next = data_in + 1
		b.next = data_add + 1

	@always(clk.posedge)
	def worker():
		data_out.next = data_in + b + (b - a)


	return instances()
	
	

@block
def tb_resize_vectors(uut, DATA_IN, DATA_IMM, MODE, DATA_OUT):
	data_in = Signal(modbv()[DATA_IN[1]:])
	data_out, data_check = [ Signal(modbv()[DATA_OUT[1]:]) for i in range(2) ]
	mode = Signal(t_lmode.LW)
	clk = Signal(bool(0))

	if (type(DATA_IMM) == type(1)) or DATA_IMM == None:
		inst_uut = uut(clk, mode, data_out, data_in, DATA_IMM)
	else:
		sig = Signal(DATA_IMM)

		inst_uut = uut(clk, mode, data_out, data_in, sig)


	@instance
	def stimulus():
		data_in.next = DATA_IN[0]
		data_check.next = DATA_OUT[0]
		mode.next = MODE
		clk.next = 0

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

# Abbrevs to make the table compact
RV = resize_vectors
RVA = resize_vectors_add
RVO = resize_vectors_op
RVS = resize_vectors_op_sane
RV1 = resize_single

CHECK_LIST = (
#     False means: We expect a ConversionError
	( True,  RV,  (0x80, 32),       None,            t_lmode.LB,  (0xffffff80, 32) ),
	( True,  RV,  (0x80, 32),       None,            t_lmode.LBU, (0x00000080, 32) ),
	( True,  RV,  (0xbeef, 32),     None,            t_lmode.LH,  (0xffffbeef, 32) ),
	( True,  RV,  (0xbeef, 32),     None,            t_lmode.LHU, (0x0000beef, 32) ),
	( True,  RV,  (0x8000beef, 32), None,            t_lmode.LW,  (0x8000beef, 32) ),
	# Adder:
	( True,  RVA, (0x80, 24),       intbv(-32)[24:], t_lmode.LW,  (0xffffc1, 24) ),
	# Make sure things don't go wrong at the bounds:
	( True,  RVA, (4, 4),   intbv(4)[4:],            t_lmode.LW,  (9, 4) ),
	# Result is truncated
	( True,  RVS, (0x80, 32),       0x0f0000,        t_lmode.LW,  (0x000080, 16) ),
	( True,  RVS, (0xdeadbeef, 32), 0x0f0000,        t_lmode.LH,  (0xffbeef, 24) ),
	( False, RVS, (0x0000beef, 24), 0x800000,        t_lmode.LH,  (0x0fbeef, 20) ),
	# Result is expanded:

	# This one is actually valid in MyHDL/Verilog, but will truncate the immediate.
	( False, RVO, (0x80, 16),       0x0f0000,        t_lmode.LW,  (0x0f0080, 24) ),

	( True,  RVS, (0x81, 16),       0x00f0f0,        t_lmode.LW,  (0x00f0f1, 24) ),

	( True,  RV1, (0x80, 24),       32,              t_lmode.LW,  (0x0000a0, 24) ),
	# Negative operands currently not supported:
	( False, RV1, (0x80, 24),       -32,             t_lmode.LW,  (0xffffe0, 24) ),

	# YET BROKEN ONES

	# This is a tricky one: Does NOT sign extend in MyHDL/Verilog, but
	# WILL sign extend in VHDL.
	( True,  RVS, (0x80, 16),       0x008000,        t_lmode.LH,  (0x008080, 24) ),
)

		

def check_resize_vectors(succeed, uut, din, imm, m, dout):
	if not succeed: # expected to throw error:
		try:
			tb_resize_vectors(uut, din, imm, m, dout).verify_convert()
		except ConversionError:
			pass
	else:
		assert tb_resize_vectors(uut, din, imm, m, dout).verify_convert() == 0


def test_resize_vectors():
	for succeed, uut, din, imm, m, dout in CHECK_LIST:
		yield check_resize_vectors, succeed, uut, din, imm, m, dout

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

	uut, din, imm, mode, dout = CHECK_LIST[10]
	tb_resize = tb_resize_vectors(uut, din, imm, mode, dout)
	tb_resize.convert("VHDL")

	return tb_resize

if __name__ == '__main__':

	tb = manual_test()

	traceSignals(tb)
	sim = Simulation(tb)
	sim.run(50000)


