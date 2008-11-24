.. currentmodule:: myhdl

.. _conv-usage:

*******************
Conversion examples
*******************


.. _conv-usage-intro:

Introduction
============

In this chapter, we will demonstrate the conversion process with a
number of examples. For the concepts of MyHDL conversion,
read the companion chapter :ref:`conv`.

.. _conv-usage-seq:

A small sequential design
=========================

Consider the following MyHDL code for an incrementer module::

  ACTIVE_LOW, INACTIVE_HIGH = 0, 1

  def Inc(count, enable, clock, reset, n):

      """ Incrementer with enable.

      count -- output
      enable -- control input, increment when 1
      clock -- clock input
      reset -- asynchronous reset input
      n -- counter max value

      """

      @always(clock.posedge, reset.negedge)
      def incLogic():
	  if reset == ACTIVE_LOW:
	      count.next = 0
	  else:
	      if enable:
		  count.next = (count + 1) % n

      return incLogic


Normally, to simulate the design, we would elaborate it as follows::

   m = 8
   n = 2 ** m

   count = Signal(intbv(0)[m:])
   enable = Signal(bool(0))
   clock, reset = [Signal(bool()) for i in range(2)]

   inc_inst = Inc(count, enable, clock, reset, n=n)

``inc_inst`` is an elaborated design instance that can be simulated. To convert
it to Verilog, we change the last line as follows::

   inc_inst = toVerilog(Inc, count, enable, clock, reset, n=n)

Again, this creates an instance that can be simulated, but as a side effect, it
also generates an equivalent Verilog module in file :file:`Inc.v`. The Verilog
code looks as follows::


    module Inc (
	count,
	enable,
	clock,
	reset
    );

    output [7:0] count;
    reg [7:0] count;
    input enable;
    input clock;
    input reset;

    always @(posedge clock, negedge reset) begin: INC_INCLOGIC
	if ((reset == 0)) begin
	    count <= 0;
	end
	else begin
	    if (enable) begin
		count <= ((count + 1) % 256);
	    end
	end
    end

    endmodule

The convertor infers a proper Verilog module interface and maps
the MyHDL generator to a Verilog always block.

Similarly, we can convert to VHDL as follows::

   inc_inst = toVHDL(Inc, count, enable, clock, reset, n=n)

This creates an equivalent VHDL module in file :file:`Inc.vhd`::


  library IEEE;
  use IEEE.std_logic_1164.all;
  use IEEE.numeric_std.all;

  use work.pck_myhdl_06.all;

  entity Inc is
      port (
	  count: inout unsigned(7 downto 0);
	  enable: in std_logic;
	  clock: in std_logic;
	  reset: in std_logic
      );
  end entity Inc;

  architecture MyHDL of Inc is

  begin

  INC_INCLOGIC: process (clock, reset) is
  begin
      if (reset = '0') then
	  count <= "00000000";
      elsif rising_edge(clock) then
	  if to_boolean(enable) then
	      count <= ((count + 1) mod 256);
	  end if;
      end if;
  end process INC_INCLOGIC;

  end architecture MyHDL;

The MyHDL generator is mapped to a VHDL process in this case.

Note that the VHDL file refers to a VHDL package called
``pck_myhdl_06``.  This package contains a number of convenience
functions that make the conversion easier.

Note also the use of an ``inout`` in the interface.  This is not
recommended VHDL design practice, but it is required here to have a
valid VHDL design that matches the behavior of the MyHDL design. As
this is only an issue for ports and as the convertor output is
non-hierarchical, the issue is not very common and has an easy
workaround.


.. _conv-usage-comb:

A small combinatorial design
============================

The second example is a small combinatorial design, more specifically the binary
to Gray code converter from previous chapters::

   def bin2gray(B, G, width):

       """ Gray encoder.

       B -- input intbv signal, binary encoded
       G -- output intbv signal, gray encoded
       width -- bit width

       """

       @always_comb
       def logic():
           Bext = intbv(0)[width+1:]
           Bext[:] = B
           for i in range(width):
               G.next[i] = Bext[i+1] ^ Bext[i]

       return logic

As before, you can create an instance and convert to Verilog and VHDL as follows::

   width = 8

   B = Signal(intbv(0)[width:])
   G = Signal(intbv(0)[width:])

   bin2gray_inst = toVerilog(bin2gray, B, G, width)
   bin2gray_inst = toVHDL(bin2gray, B, G, width)

The generated Verilog code looks as follows::

  module bin2gray (
      B,
      G
  );

  input [7:0] B;
  output [7:0] G;
  reg [7:0] G;


  always @(B) begin: BIN2GRAY_LOGIC
      integer i;
      reg [9-1:0] Bext;
      Bext = 9'h0;
      Bext = B;
      for (i=0; i<8; i=i+1) begin
	  G[i] <= (Bext[(i + 1)] ^ Bext[i]);
      end
  end

  endmodule


The generated VHDL code looks as follows::


  library IEEE;
  use IEEE.std_logic_1164.all;
  use IEEE.numeric_std.all;
  use std.textio.all;

  use work.pck_myhdl_06.all;

  entity bin2gray is
      port (
	  B: in unsigned(7 downto 0);
	  G: out unsigned(7 downto 0)
      );
  end entity bin2gray;

  architecture MyHDL of bin2gray is

  begin

  BIN2GRAY_LOGIC: process (B) is
      variable Bext: unsigned(8 downto 0);
  begin
      Bext := to_unsigned(0, 9);
      Bext := resize(B, 9);
      for i in 0 to 8-1 loop
	  G(i) <= (Bext((i + 1)) xor Bext(i));
      end loop;
  end process BIN2GRAY_LOGIC;

  end architecture MyHDL;



.. _conv-usage-hier:

A hierarchical design
=====================

The converter can handle designs with an arbitrarily deep hierarchy.

For example, suppose we want to design an incrementer with Gray code output.
Using the designs from previous sections, we can proceed as follows::


   def GrayInc(graycnt, enable, clock, reset, width):

       bincnt = Signal(intbv(0)[width:])

       inc_1 = inc(bincnt, enable, clock, reset, n=2**width)
       bin2gray_1 = bin2gray(B=bincnt, G=graycnt, width=width)

       return inc_1, bin2gray_1

According to Gray code properties, only a single bit will change in consecutive
values. However, as the ``bin2gray`` module is combinatorial, the output bits
may have transient glitches, which may not be desirable. To solve this, let's
create an additional level of hierarchy and add an output register to the
design. (This will create an additional latency of a clock cycle, which may not
be acceptable, but we will ignore that here.) ::

   def GrayIncReg(graycnt, enable, clock, reset, width):

       graycnt_comb = Signal(intbv(0)[width:])

       gray_inc_1 = GrayInc(graycnt_comb, enable, clock, reset, width)

       @always(clock.posedge)
       def reg_1():
           graycnt.next = graycnt_comb

       return gray_inc_1, reg_1

We can convert this hierarchical design as before::

   width = 8
   graycnt = Signal(intbv()[width:])
   enable, clock, reset = [Signal(bool()) for i in range(3)]
   toVerilog(GrayIncReg, graycnt, enable, clock, reset, width)
   toVHDL(GrayIncReg, graycnt, enable, clock, reset, width)


The Verilog output code looks as follows::

    module GrayIncReg (
	graycnt,
	enable,
	clock,
	reset
    );

    output [7:0] graycnt;
    reg [7:0] graycnt;
    input enable;
    input clock;
    input reset;

    reg [7:0] graycnt_comb;
    reg [7:0] gray_inc_1_bincnt;



    always @(posedge clock, negedge reset) begin: GRAYINCREG_GRAY_INC_1_INC_1_INCLOGIC
	if ((reset == 0)) begin
	    gray_inc_1_bincnt <= 0;
	end
	else begin
	    if (enable) begin
		gray_inc_1_bincnt <= ((gray_inc_1_bincnt + 1) % 256);
	    end
	end
    end

    always @(gray_inc_1_bincnt) begin: GRAYINCREG_GRAY_INC_1_BIN2GRAY_1_LOGIC
	integer i;
	reg [9-1:0] Bext;
	Bext = 9'h0;
	Bext = gray_inc_1_bincnt;
	for (i=0; i<8; i=i+1) begin
	    graycnt_comb[i] <= (Bext[(i + 1)] ^ Bext[i]);
	end
    end

    always @(posedge clock) begin: GRAYINCREG_REG_1
	graycnt <= graycnt_comb;
    end

    endmodule


The VHDL output code looks as follows::

    library IEEE;
    use IEEE.std_logic_1164.all;
    use IEEE.numeric_std.all;

    use work.pck_myhdl_06.all;

    entity GrayIncReg is
	port (
	    graycnt: out unsigned(7 downto 0);
	    enable: in std_logic;
	    clock: in std_logic;
	    reset: in std_logic
	);
    end entity GrayIncReg;

    architecture MyHDL of GrayIncReg is

    signal graycnt_comb: unsigned(7 downto 0);
    signal gray_inc_1_bincnt: unsigned(7 downto 0);

    begin


    GRAYINCREG_GRAY_INC_1_INC_1_INCLOGIC: process (clock, reset) is
    begin
	if (reset = '0') then
	    gray_inc_1_bincnt <= "00000000";
	elsif rising_edge(clock) then
	    if to_boolean(enable) then
		gray_inc_1_bincnt <= ((gray_inc_1_bincnt + 1) mod 256);
	    end if;
	end if;
    end process GRAYINCREG_GRAY_INC_1_INC_1_INCLOGIC;

    GRAYINCREG_GRAY_INC_1_BIN2GRAY_1_LOGIC: process (gray_inc_1_bincnt) is
	variable Bext: unsigned(8 downto 0);
    begin
	Bext := to_unsigned(0, 9);
	Bext := resize(gray_inc_1_bincnt, 9);
	for i in 0 to 8-1 loop
	    graycnt_comb(i) <= (Bext((i + 1)) xor Bext(i));
	end loop;
    end process GRAYINCREG_GRAY_INC_1_BIN2GRAY_1_LOGIC;

    GRAYINCREG_REG_1: process (clock) is
    begin
	if rising_edge(clock) then
	    graycnt <= graycnt_comb;
	end if;
    end process GRAYINCREG_REG_1;

    end architecture MyHDL;


Note that the output is a flat "net list of blocks", and that hierarchical
signal names are generated as necessary.


.. _conv-usage-fsm:

Optimizations for finite state machines
=======================================

As often in hardware design, finite state machines deserve special attention.

In Verilog and VHDL, finite state machines are typically described using case
statements.  Python doesn't have a case statement, but the converter recognizes
particular if-then-else structures and maps them to case statements. This
optimization occurs when a variable whose type is an enumerated type is
sequentially tested against enumeration items in an if-then-else structure.
Also, the appropriate synthesis pragmas for efficient synthesis are generated in
the Verilog code.

As a further optimization, function :func:`enum` was enhanced to support
alternative encoding schemes elegantly, using an additional parameter
*encoding*. For example::

   t_State = enum('SEARCH', 'CONFIRM', 'SYNC', encoding='one_hot')

The default encoding is ``'binary'``; the other possibilities are ``'one_hot'``
and ``'one_cold'``. This parameter only affects the conversion output, not the
behavior of the type.  The generated Verilog code for case statements is
optimized for an efficient implementation according to the encoding. Note that
in contrast, a Verilog designer has to make nontrivial code changes to implement
a different encoding scheme.

As an example, consider the following finite state machine, whose state variable
uses the enumeration type defined above::

  ACTIVE_LOW = bool(0)
  FRAME_SIZE = 8
  t_State = enum('SEARCH', 'CONFIRM', 'SYNC', encoding="one_hot")

  def FramerCtrl(SOF, state, syncFlag, clk, reset_n):

      """ Framing control FSM.

      SOF -- start-of-frame output bit
      state -- FramerState output
      syncFlag -- sync pattern found indication input
      clk -- clock input
      reset_n -- active low reset

      """

      index = Signal(intbv(0)[8:]) # position in frame

      @always(clk.posedge, reset_n.negedge)
      def FSM():
	  if reset_n == ACTIVE_LOW:
	      SOF.next = 0
	      index.next = 0
	      state.next = t_State.SEARCH
	  else:
	      index.next = (index + 1) % FRAME_SIZE
	      SOF.next = 0
	      if state == t_State.SEARCH:
		  index.next = 1
		  if syncFlag:
		      state.next = t_State.CONFIRM
	      elif state == t_State.CONFIRM:
		  if index == 0:
		      if syncFlag:
			  state.next = t_State.SYNC
		      else:
			  state.next = t_State.SEARCH
	      elif state == t_State.SYNC:
		  if index == 0:
		      if not syncFlag:
			  state.next = t_State.SEARCH
		  SOF.next = (index == FRAME_SIZE-1)
	      else:
		  raise ValueError("Undefined state")

      return FSM


The conversion is done as before::

   SOF = Signal(bool(0))
   syncFlag = Signal(bool(0))
   clk = Signal(bool(0))
   reset_n = Signal(bool(1))
   state = Signal(t_State.SEARCH)
   toVerilog(FramerCtrl, SOF, state, syncFlag, clk, reset_n)
   toVHDL(FramerCtrl, SOF, state, syncFlag, clk, reset_n)


The Verilog output looks as follows::

    module FramerCtrl (
	SOF,
	state,
	syncFlag,
	clk,
	reset_n
    );

    output SOF;
    reg SOF;
    output [2:0] state;
    reg [2:0] state;
    input syncFlag;
    input clk;
    input reset_n;

    reg [7:0] index;



    always @(posedge clk, negedge reset_n) begin: FRAMERCTRL_FSM
	if ((reset_n == 0)) begin
	    SOF <= 0;
	    index <= 0;
	    state <= 3'b001;
	end
	else begin
	    index <= ((index + 1) % 8);
	    SOF <= 0;
	    // synthesis parallel_case full_case
	    casez (state)
		3'b??1: begin
		    index <= 1;
		    if (syncFlag) begin
			state <= 3'b010;
		    end
		end
		3'b?1?: begin
		    if ((index == 0)) begin
			if (syncFlag) begin
			    state <= 3'b100;
			end
			else begin
			    state <= 3'b001;
			end
		    end
		end
		3'b1??: begin
		    if ((index == 0)) begin
			if ((!syncFlag)) begin
			    state <= 3'b001;
			end
		    end
		    SOF <= (index == (8 - 1));
		end
		default: begin
		    $finish;
		end
	    endcase
	end
    end

    endmodule

The VHDL output looks as follows::

    package pck_FramerCtrl is

	type t_enum_t_State_1 is (
	SEARCH,
	CONFIRM,
	SYNC
    );
    attribute enum_encoding of t_enum_t_State_1: type is "001 010 100";

    end package pck_FramerCtrl;

    library IEEE;
    use IEEE.std_logic_1164.all;
    use IEEE.numeric_std.all;
    use std.textio.all;

    use work.pck_myhdl_06.all;

    use work.pck_FramerCtrl.all;

    entity FramerCtrl is
	port (
	    SOF: out std_logic;
	    state: inout t_enum_t_State_1;
	    syncFlag: in std_logic;
	    clk: in std_logic;
	    reset_n: in std_logic
	);
    end entity FramerCtrl;

    architecture MyHDL of FramerCtrl is

    signal index: unsigned(7 downto 0);

    begin


    FRAMERCTRL_FSM: process (clk, reset_n) is
    begin
	if (reset_n = '0') then
	    SOF <= '0';
	    index <= "00000000";
	    state <= SEARCH;
	elsif rising_edge(clk) then
	    index <= ((index + 1) mod 8);
	    SOF <= '0';
	    case state is
		when SEARCH =>
		    index <= "00000001";
		    if to_boolean(syncFlag) then
			state <= CONFIRM;
		    end if;
		when CONFIRM =>
		    if (index = 0) then
			if to_boolean(syncFlag) then
			    state <= SYNC;
			else
			    state <= SEARCH;
			end if;
		    end if;
		when SYNC =>
		    if (index = 0) then
			if (not to_boolean(syncFlag)) then
			    state <= SEARCH;
			end if;
		    end if;
		    SOF <= to_std_logic(signed(resize(index, 9)) = (8 - 1));
		when others =>
		    assert False report "End of Simulation" severity Failure;
	    end case;
	end if;
    end process FRAMERCTRL_FSM;

    end architecture MyHDL;


.. _conv-usage-ram:

RAM inference
=============

Certain synthesis tools can infer RAM structures. To support
this feature, the converter maps lists of signals in MyHDL
to Verilog memories and VHDL arrays.

The following MyHDL example is a ram model that uses a list of signals to model
the internal memory. ::

   def RAM(dout, din, addr, we, clk, depth=128):
       """  Ram model """

       mem = [Signal(intbv(0)[8:]) for i in range(depth)]

       @always(clk.posedge)
       def write():
           if we:
               mem[int(addr)].next = din

       @always_comb
       def read():
           dout.next = mem[int(addr)]

       return write, read

With the appropriate signal definitions for the interface ports, it is converted
to the following Verilog code. Note how the list of signals ``mem`` is mapped to
a Verilog memory. ::

    module ram (
	dout,
	din,
	addr,
	we,
	clk
    );

    output [7:0] dout;
    wire [7:0] dout;
    input [7:0] din;
    input [6:0] addr;
    input we;
    input clk;


    reg [7:0] mem [0:128-1];


    always @(posedge clk) begin: RAM_1_WRITE
	if (we) begin
	    mem[addr] <= din;
	end
    end


    assign dout = mem[addr];

    endmodule

In VHDL, the list of MyHDL signals is modeled as a VHDL array signal::

    library IEEE;
    use IEEE.std_logic_1164.all;
    use IEEE.numeric_std.all;

    use work.pck_myhdl_06.all;

    entity ram is
	port (
	    dout: out unsigned(7 downto 0);
	    din: in unsigned(7 downto 0);
	    addr: in unsigned(6 downto 0);
	    we: in std_logic;
	    clk: in std_logic
	);
    end entity ram;

    architecture MyHDL of ram is

    type t_array_mem is array(0 to 128-1) of unsigned(7 downto 0);
    signal mem: t_array_mem;

    begin

    RAM_WRITE: process (clk) is
    begin
	if rising_edge(clk) then
	    if to_boolean(we) then
		mem(to_integer(addr)) <= din;
	    end if;
	end if;
    end process RAM_WRITE;


    dout <= mem(to_integer(addr));

    end architecture MyHDL;



.. _conv-usage-rom:

ROM inference
=============

Some synthesis tools can infer a ROM memory from a case statement. The Verilog
converter can perform the expansion into a case statement automatically, based
on a higher level description. The ROM access is described in a single line, by
indexing into a tuple of integers. The tuple can be described manually, but also
by programmatical means. Note that a tuple is used instead of a list to stress
the read-only character of the memory.

The following example illustrates this functionality. ROM access is described as
follows::

   def rom(dout, addr, CONTENT):

       @always_comb
       def read():
           dout.next = CONTENT[int(addr)]

       return read

The ROM content is described as a tuple of integers. When the ROM content is
defined, the conversion can be performed::

   CONTENT = (17, 134, 52, 9)
   dout = Signal(intbv(0)[8:])
   addr = Signal(intbv(0)[4:])

   toVerilog(rom, dout, addr, CONTENT)
   toVHDL(rom, dout, addr, CONTENT)

The Verilog output code is as follows::

    module rom (
	dout,
	addr
    );

    output [7:0] dout;
    reg [7:0] dout;
    input [3:0] addr;

    always @(addr) begin: ROM_READ
	// synthesis parallel_case full_case
	case (addr)
	    0: dout <= 17;
	    1: dout <= 134;
	    2: dout <= 52;
	    default: dout <= 9;
	endcase
    end

    endmodule


The VHDL output code is as follows::


    library IEEE;
    use IEEE.std_logic_1164.all;
    use IEEE.numeric_std.all;
    use std.textio.all;

    use work.pck_myhdl_06.all;

    entity rom is
	port (
	    dout: out unsigned(7 downto 0);
	    addr: in unsigned(3 downto 0)
	);
    end entity rom;

    architecture MyHDL of rom is


    begin

    ROM_READ: process (addr) is
    begin
	case to_integer(addr) is
	    when 0 => dout <= "00010001";
	    when 1 => dout <= "10000110";
	    when 2 => dout <= "00110100";
	    when others => dout <= "00001001";
	end case;
    end process ROM_READ;

    end architecture MyHDL;


.. _conv-usage-custom:

User-defined code
=================

MyHDL provides a way to include user-defined code during the
conversion process, using the ``__verilog__`` and ``__vhdl__``
hooks. 

For example::

    def inc_comb(nextCount, count, n):

	@always(count)
	def logic():
	    # do nothing here
	    pass

	nextCount.driven = "wire"

	__verilog__ =\
    """
    assign %(nextCount)s = (%(count)s + 1) %% %(n)s;
    """

	__vhdl__ =\
    """
    %(nextCount)s <= (%(count)s + 1) mod %(n)s;
    """

	return logic

The converted code looks as follows in Verilog::

    module inc_comb (
	nextCount,
	count
    );

    output [7:0] nextCount;
    wire [7:0] nextCount;
    input [7:0] count;

    assign nextCount = (count + 1) % 256;

    endmodule

and as follows in VHDL::

    library IEEE;
    use IEEE.std_logic_1164.all;
    use IEEE.numeric_std.all;

    use work.pck_myhdl_06.all;

    entity inc_comb is
	port (
	    nextCount: out unsigned(7 downto 0);
	    count: in unsigned(7 downto 0)
	);
    end entity inc_comb;

    architecture MyHDL of inc_comb is

    begin

    nextCount <= (count + 1) mod 256;

    end architecture MyHDL;


In this example, conversion of the :func:`inc_comb` function is
bypassed and the user-defined code is inserted instead. Note that the
user-defined code refers to signals and parameters in the MyHDL
context by using format specifiers. During conversion, the appropriate
hierarchical names and parameter values will be filled in. Note
that the format specifier indicator % needs to be escaped (by doubling
it) if it is required in the user-defined code.

The MyHDL code contains the following assignment::

   nextCount.driven = "wire"

This specifies that the nextCount signal is driven as a Verilog wire from this
module.

For more info about user-defined code, see :ref:`conv-custom`.
