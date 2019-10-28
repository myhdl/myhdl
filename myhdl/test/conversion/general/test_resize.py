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
def resize_vectors(clk, mode, data_out, data_in):
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
def tb_resize_vectors(DATA_IN, MODE, DATA_OUT):
	data_in, data_out, data_check = [ Signal(modbv()[32:]) for i in range(3) ]
	mode = Signal(t_lmode.LW)
	clk = Signal(bool(0))

	inst_uut = resize_vectors(clk, mode, data_out, data_in)

	@instance
	def clkgen():
		while 1:
			yield delay(10)
			clk.next = not clk

	@instance
	def stimulus():
		data_in.next = DATA_IN
		data_check.next = DATA_OUT
		mode.next = MODE
		yield clk.posedge
		yield clk.posedge

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
		else:
			print("FAIL")
			print(data_out)
			raise ValueError("resize error, result %x" % data_out)

		raise StopSimulation

	return instances()

CHECK_LIST = (
		( 0x80,       t_lmode.LB,  0xffffff80 ),
		( 0x80,       t_lmode.LBU, 0x00000080 ),
		( 0xbeef,     t_lmode.LH,  0xffffbeef ),
		( 0xbeef,     t_lmode.LHU, 0x0000beef ),
		( 0x8000beef, t_lmode.LW,  0x8000beef ),
)

		
@block
def tb_myhdl_resize_vectors():

	data_in, data_out, data_check = [ Signal(modbv()[32:]) for i in range(3) ]
	mode = Signal(t_lmode.LW)
	clk = Signal(bool(0))

	inst_uut = resize_vectors(clk, mode, data_out, data_in)

	@instance
	def clkgen():
		while 1:
			yield delay(10)
			clk.next = not clk

	@instance
	def stimulus():
		for DATA_IN, MODE, DATA_OUT in CHECK_LIST:
			data_in.next = DATA_IN
			data_check.next = DATA_OUT
			mode.next = MODE
			yield clk.posedge
			yield clk.posedge
			if data_out == data_check:
				print("mode: %s" % mode)
			else:
				raise ValueError("resize error, result %x" % data_out)

		raise StopSimulation

	return instances()
		

def check_resize_vectors(din, m, dout):
	assert tb_resize_vectors(din, m, dout).verify_convert() == 0

def test_resize_vectors():
	for din, m, dout in CHECK_LIST:
		yield check_resize_vectors, din, m, dout

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
	data_in, data_out, data_check = [ Signal(modbv()[32:]) for i in range(3) ]
	mode = Signal(t_lmode.LW)
	clk = Signal(bool(0))

	tb_resize = tb_resize_vectors(0x80, t_lmode.LB, 0xffffff80)
	tb.resize.convert("VHDL")

if __name__ == '__main__':

	tb = traceSignals(tb_myhdl_resize_vectors)
	sim = Simulation(tb)
	sim.run(50000)

	manual_test()

