from myhdl import *

"""Test case #286 (hackfin@section5.ch)

Top level ports should be converted to a consistent scheme, no matter
what the hierarchy inside the @block is like.

Note: Collides with general/test_interface2.py
"""

class Port:
	def __init__(self, tmpl):
		self.reset = ResetSignal(0, 1, isasync = True)
		self.foo = Signal(bool(0))
		self.bar = Signal(bool(0))
		self.dout = Signal(bool(0))
		self.blaa   = Signal(tmpl)

@block
def ff(clk, pin, out):
	tmp = Signal(bool(0))

	@always(clk.posedge)
	def worker():
		out.next = pin

	return instances()

@block
def dummy(clk, port, out):
	@always(clk.posedge)
	def worker():
		if port.blaa == 0:
			out.next = port.bar
	return instances()
		
@block
def Unit(clk, port):
	out0 = Signal(bool(0))
	out1 = Signal(bool(0))

	ff1 = ff(clk, port.foo, out0)
	d = dummy(clk, port, out1)

	@always(clk.posedge)
	def worker():
		if port.reset:
			port.dout.next = 0
		else:
			port.dout.next = port.foo or out0 or out1

	return instances()

@block
def wrapper(clk, reset, foo, bar, blaa):
	"Bare VHDL wrapper generated in MyHDL for test"

	@always(clk.posedge)
	def dummy():
		pass

	return instances()

wrapper.vhdl_code = \
"""

unit_wrap: entity work.Unit
	port map (
		port_reset    => $reset,
		port_blaa     => $blaa,
		port_foo      => $foo,
		port_bar      => $bar,
		clk           => $clk
	);

"""

@block
def tb_wrapper(clk, reset, foo, bar, blaa):
	"Main block to create wrapper and a Unit instance"

	uut = wrapper(clk, reset, foo, bar, blaa)
	
	@instance
	def dummy():
		print("TEST start")
		clk.next = 0
		yield delay(10)
		clk.next = 1
		print("TEST done")

	return instances()

def test_convert():
	clk = Signal(bool(0))
	reset = Signal(bool(0))
	foo, bar = [ Signal(bool(0)) for i in range(2) ]
	blaa = Signal(intbv(0x00)[8:])

	clk = Signal(bool(0))
	port = Port(intbv(0x00)[8:])
	u = Unit(clk, port)

	u.convert(hdl="VHDL")
	# unit_file = open("Unit.vhd")
	# unit_vhdl = unit_file.read()
	# unit_file.close()

	tb = tb_wrapper(clk, reset, foo, bar, blaa)

	assert tb.verify_convert("Unit.vhd") == 0


