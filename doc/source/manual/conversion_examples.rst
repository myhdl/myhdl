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

   def inc(count, enable, clock, reset, n):

       """ Incrementer with enable.

       count -- output
       enable -- control input, increment when 1
       clock -- clock input
       reset -- asynchronous reset input
       n -- counter max value

       """

       @always(clock.posedge, reset.negedge)
       def incProcess():
           if reset == ACTIVE_LOW:
               count.next = 0
           else:
               if enable:
                   count.next = (count + 1) % n

       return incProcess

In Verilog terminology, function :func:`inc` corresponds to a module, while the
decorated function :func:`incProcess` roughly corresponds to an always block.

Normally, to simulate the design, we would "elaborate" an instance as follows::

   m = 8
   n = 2 ** m

   count = Signal(intbv(0)[m:])
   enable = Signal(bool(0))
   clock, reset = [Signal(bool()) for i in range(2)]

   inc_inst = inc(count, enable, clock, reset, n=n)

``inc_inst`` is an elaborated design instance that can be simulated. To convert
it to Verilog, we change the last line as follows::

   inc_inst = toVerilog(inc, count, enable, clock, reset, n=n)

Again, this creates an instance that can be simulated, but as a side effect, it
also generates an equivalent Verilog module in file :file:`inc.v`. The Verilog
code looks as follows::

   module inc_inst (
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


   always @(posedge clock or negedge reset) begin: _MYHDL1_BLOCK
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

You can see the module interface and the always block, as expected from the
MyHDL design.


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

As before, you can create an instance and convert to Verilog as follows::

   width = 8

   B = Signal(intbv(0)[width:])
   G = Signal(intbv(0)[width:])

   bin2gray_inst = toVerilog(bin2gray, B, G, width)

The generated Verilog code looks as follows::

   module bin2gray (
       B,
       G
   );

   input [7:0] B;
   output [7:0] G;
   reg [7:0] G;

   always @(B) begin: _bin2gray_logic
       integer i;
       reg [9-1:0] Bext;
       Bext = 9'h0;
       Bext = B;
       for (i=0; i<8; i=i+1) begin
           G[i] <= (Bext[(i + 1)] ^ Bext[i]);
       end
   end

   endmodule


.. _conv-usage-hier:

A hierarchical design
=====================

The Verilog converter can handle designs with an arbitrarily deep hierarchy.

For example, suppose we want to design an incrementer with Gray code output.
Using the designs from previous sections, we can proceed as follows::

   ACTIVE_LOW, INACTIVE_HIGH = 0, 1

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

   gray_inc_reg_1 = toVerilog(GrayIncReg, graycnt, enable, clock, reset, width)

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
   reg [7:0] _gray_inc_1_bincnt;


   always @(posedge clock or negedge reset) begin: _GrayIncReg_gray_inc_1_inc_1_incProcess
       if ((reset == 0)) begin
           _gray_inc_1_bincnt <= 0;
       end
       else begin
           if (enable) begin
               _gray_inc_1_bincnt <= ((_gray_inc_1_bincnt + 1) % 256);
           end
       end
   end

   always @(_gray_inc_1_bincnt) begin: _GrayIncReg_gray_inc_1_bin2gray_1_logic
       integer i;
       reg [9-1:0] Bext;
       Bext = 9'h0;
       Bext = _gray_inc_1_bincnt;
       for (i=0; i<8; i=i+1) begin
           graycnt_comb[i] <= (Bext[(i + 1)] ^ Bext[i]);
       end
   end

   always @(posedge clock) begin: _GrayIncReg_reg_1
       graycnt <= graycnt_comb;
   end

   endmodule

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

   ACTIVE_LOW = 0
   FRAME_SIZE = 8

   def FramerCtrl(SOF, state, syncFlag, clk, reset_n, t_State):

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
   framerctrl_inst = toVerilog(FramerCtrl, SOF, state, syncFlag, clk, reset_n)

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


   always @(posedge clk or negedge reset_n) begin: _FramerCtrl_FSM
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
                   $display("ValueError(Undefined state)");
                   $finish;
               end
           endcase
       end
   end

   endmodule


.. _conf-usage-ram:

RAM inference
=============

Certain synthesis tools can map Verilog memories to RAM structures. To support
this interesting feature, the Verilog converter maps lists of signals in MyHDL
to Verilog memories.

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

   module RAM (
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

   always @(posedge clk) begin: _RAM_write
       if (we) begin
           mem[addr] <= din;
       end
   end

   assign dout = mem[addr];

   endmodule


.. _conf-usage-rom:

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

The Verilog output code is as follows::

   module rom (
       dout,
       addr
   );

   output [7:0] dout;
   reg [7:0] dout;
   input [3:0] addr;

   always @(addr) begin: _rom_read
       // synthesis parallel_case full_case
       case (addr)
           0: dout <= 17;
           1: dout <= 134;
           2: dout <= 52;
           default: dout <= 9;
       endcase
   end

   endmodule


.. _conf-usage-custom:

User-defined code
=================

MyHDL provides a way  to include user-defined Verilog code during the conversion
process.

MyHDL defines a hook that is understood by the converter but ignored by the
simulator. The hook is called ``__verilog__``. It operates like a special return
value. When a MyHDL function defines ``__verilog__``, the Verilog converter will
use its value instead of the regular return value.

The value of ``__verilog__`` should be a format string that uses keys in its
format specifiers. The keys refer to the variable names in the context of the
string.

Example::

   def inc_comb(nextCount, count, n):

       @always_comb
       def logic():
           # note: '-' instead of '+'
           nextCount.next = (count - 1) % n

       nextCount.driven = "wire"

       __verilog__ =\
   """
   assign %(nextCount)s = (%(count)s + 1) %% %(n)s;
   """

       return logic

The converted code looks as follows::

   module inc_comb (
       nextCount,
       count
   );

   output [7:0] nextCount;
   wire [7:0] nextCount;
   input [7:0] count;

   assign nextCount = (count + 1) % 128;

   endmodule

In this example, conversion of the :func:`inc_comb` function is bypassed and the
user-defined Verilog code is inserted instead. Note that the user-defined code
refers to signals and parameters in the MyHDL context by using format
specifiers. During conversion, the appropriate hierarchical names and parameter
values will be filled in. Note also that the format specifier indicator % needs
to be escaped (by doubling it) if it is required in the user-defined code.

There is one more issue that needs user attention. Normally, the Verilog
converter infers inputs, internal signals, and outputs. It also detects undriven
and multiple driven signals. To do this, it assumes that signals are not driven
by default. It then processes the code to find out which signals are driven from
where. However, it cannot do this for user-defined code. Without additional
help, this will result in warnings or errors during the inference process, or in
compilation errors from invalid Verilog code. The user should solve this by
setting the ``driven`` attribute for signals that are driven from the user-
defined code. In the example code above, note the following assignment::

   nextCount.driven = "wire"

This specifies that the nextCount signal is driven as a Verilog wire from this
module. The allowed values of the driven attribute are ``'wire'`` and ``'reg'``.
The value specifies how the user-defined Verilog code drives the signal in
Verilog. To decide which value to use, consider how the signal should be
declared in Verilog after the user-defined code is inserted.


