
.. _conv:

*********************
Conversion to Verilog
*********************


.. _conv-intro:

Introduction
============

MyHDL supports the automatic conversion of implementation-oriented MyHDL code to
Verilog code. This feature provides a direct path from Python to an FPGA or ASIC
implementation.


.. _conv-solution:

Solution description
====================

The solution works as follows. The hardware description should satisfy certain
constraints that are typical for implementation-oriented hardware modeling.
Subsequently, such a design is converted to an equivalent model in the Verilog
language, using the function :func:`toVerilog` from the MyHDL\ library. Finally,
a third-party *synthesis tool* is used to convert the Verilog design to a gate
implementation for an ASIC or FPGA. There are a number of Verilog synthesis
tools available, varying in price, capabilities, and target implementation
technology.

The conversion does not start from source files, but from an instantiated design
that has been *elaborated* by the Python interpreter. The converter uses the
Python profiler to track the interpreter's operation and to infer the design
structure and name spaces. It then selectively compiles pieces of source code
for additional analysis and for conversion. This is done using the Python
compiler package.


.. _conv-features:

Features
========


.. _conv-features-elab:

The design is converted after elaboration
-----------------------------------------

*Elaboration* refers to the initial processing of a hardware description to
achieve a representation of a design instance that is ready for simulation or
synthesis. In particular, structural parameters and constructs are processed in
this step. In MyHDL, the Python interpreter itself is used for elaboration.  A
:class:`Simulation` object is constructed with elaborated design instances as
arguments.  Likewise, the Verilog conversion works on an elaborated design
instance. The Python interpreter is thus used as much as possible.


.. _conv-features-struc:

The structural description can be arbitrarily complex and hierarchical
----------------------------------------------------------------------

As the conversion works on an elaborated design instance, any modeling
constraints only apply to the leaf elements of the design structure, that is,
the co-operating generators. In other words, there are no restrictions on the
description of the design structure: Python's full power can be used for that
purpose. Also, the design hierarchy can be arbitrarily deep.


.. _conv-features-gen:

Generators are mapped to Verilog always or initial blocks
---------------------------------------------------------

The converter analyzes the code of each generator and maps it to a Verilog
``always`` blocks if possible, and to  an ``initial`` block otherwise. The
converted Verilog design will be a flat "net list of blocks".


.. _conv-features-intf:

The Verilog module interface is inferred from signal usage
----------------------------------------------------------

In MyHDL, the input or output direction of interface signals is not explicitly
declared. The converter investigates signal usage in the design hierarchy to
infer whether a signal is used as input, output, or as an internal signal.
Internal signals are given a hierarchical name in the Verilog output.


.. _conv-features-func:

Function calls are mapped to a unique Verilog function or task call
-------------------------------------------------------------------

The converter analyzes function calls and function code to see if they should be
mapped to Verilog functions or to tasks. Python functions are much more powerful
than Verilog subprograms; for example, they are inherently generic, and they can
be called with named association.  To support this power in Verilog, a unique
Verilog function or task is generated per Python function call.


.. _conv-features-if:

If-then-else structures may be mapped to Verilog case statements
----------------------------------------------------------------

Python does not provide a case statement. However,  the converter recognizes if-
then-else structures in which a variable is sequentially compared to items of an
enumeration type, and maps such a structure to a Verilog case statement with the
appropriate synthesis attributes.


.. _conv-features-enum:

Choice of encoding schemes for enumeration types
------------------------------------------------

The :func:`enum` function in MyHDL returns an enumeration type. This function
takes an additional parameter *encoding* that specifies the desired encoding in
the implementation: binary, one hot, or one cold. The Verilog converter
generates the appropriate code.


.. _conf-features-ram:

Support for RAM inference
-------------------------

Certain synthesis tools can map Verilog memories to RAM structures. To support
this interesting feature, the Verilog converter maps lists of signals to Verilog
memories.


.. _conf-features-rom:

Support for ROM memory
----------------------

Some synthesis tools can infer a ROM from a case statement. The Verilog
converter does the expansion into a case statement automatically, based on a
higher level description. The ROM access is described in a single line, by
indexing into a tuple of integers.


.. _conf-features-signed:

Support for signed arithmetic
-----------------------------

In MyHDL, working with negative numbers is trivial: one just uses ``intbv``
objects with negative values. By contrast, negative numbers are tricky in
Verilog. The language makes a difference between an unsigned and a signed
representation, and the user has to declare signed variables explicitly.  When
the two representations are mixed in an expression, all operands are interpreted
as unsigned, which typically leads to unexpected results.

The Verilog converter handles negative ``intbv`` objects by using a signed
Verilog representation. Also, it automatically performs sign extension and
casting to a signed representation when unsigned numbers are used in a mixed
expression. In this way, it automates a task which is notoriously hard to get
right in Verilog directly.


.. _conf-features-udfv:

Support for user-defined Verilog code
-------------------------------------

If desired, the user can bypass the regular Verilog conversion and describe
user-defined code to be inserted instead.


.. _conv-subset:

The convertible subset
======================


.. _conv-subset-intro:

Introduction
------------

Unsurprisingly, not all MyHDL code can be converted to Verilog. In fact, there
are very important restrictions.  As the goal of the conversion functionality is
implementation, this should not be a big issue: anyone familiar with synthesis
is used to similar restrictions in the *synthesizable subset* of Verilog and
VHDL. The converter attempts to issue clear error messages when it encounters a
construct that cannot be converted.

In practice, the synthesizable subset usually refers to RTL synthesis, which is
by far the most popular type of synthesis today. There are industry standards
that define the RTL synthesis subset.  However, those were not used as a model
for the restrictions of the MyHDL converter, but as a minimal starting point.
On that basis, whenever it was judged easy or useful to support an additional
feature, this was done. For example, it is actually easier to convert
:keyword:`while` loops than :keyword:`for` loops even though they are not RTL-
synthesizable.  As another example, :keyword:`print` is supported because it's
so useful for debugging, even though it's not synthesizable.  In summary, the
convertible subset is a superset of the standard RTL synthesis subset, and
supports synthesis tools with more advanced capabilities, such as behavioral
synthesis.

Recall that any restrictions only apply to the design post elaboration.  In
practice, this means that they apply only to the code of the generators, that
are the leaf functional blocks in a MyHDL design.


.. _conv-subset-style:

Coding style
------------

A natural restriction on convertible code is that it should be written in MyHDL
style: cooperating generators, communicating through signals, and with
sensitivity lists specifying wait points and resume conditions.  Supported
resume conditions are a signal edge, a signal change, or a tuple of such
conditions.


.. _conv-subset-types:

Supported types
---------------

The most important restriction regards object types. Verilog is an almost
typeless language, while Python is strongly (albeit dynamically) typed. The
converter has to infer the types of names used in the code, and map those names
to Verilog variables.

Only a limited amount of types can be converted. Python :class:`int` and
:class:`long` objects are mapped to Verilog integers. All other supported types
are mapped to Verilog regs (or wires), and therefore need to have a defined bit
width. The supported types are the Python :class:`bool` type, the MyHDL
:class:`intbv` type, and MyHDL enumeration types returned by function
:func:`enum`. The latter objects can also be used as the base object of a
:class:`Signal`.

:class:`intbv` objects must be constructed so that a bit width can be inferred.
This can be done by specifying minimum and maximum values, e.g. as follows::

   index = intbv(0, min=MIN, max=MAX)

The Verilog converter supports :class:`intbv` objects that can take negative
values.

Alternatively, a slice can be taken from an :class:`intbv` object as follows::

   index = intbv(0)[N:]

Such as slice returns a new :class:`intbv` object, with minimum value ``0`` ,
and maximum value ``2**N``.


.. _conv-subset-statements:

Supported statements
--------------------

The following is a list of the statements that are supported by the Verilog
converter, possibly qualified with restrictions or usage notes.

:keyword:`break`

:keyword:`continue`

:keyword:`def`

:keyword:`for`
   The only supported iteration scheme is iterating through sequences of integers
   returned by built-in function :func:`range` or MyHDL\ function
   :func:`downrange`.  The optional :keyword:`else` clause is not supported.

:keyword:`if`
   :keyword:`if`, :keyword:`elif`, and :keyword:`else` clauses are fully supported.

:keyword:`pass`

:keyword:`print`
   When printing an interpolated string, the format specifiers are copied verbatim
   to the Verilog output.  Printing to a file (with syntax ``'>>'``) is not
   supported.

:keyword:`raise`
   This statement is mapped to Verilog statements that end the simulation with an
   error message.

:keyword:`return`

:keyword:`yield`
   The yielded expression can be a signal, a signal edge as specified by MyHDL
   functions :func:`posedge` or :func:`negedge`, or a tuple of signals and edge
   specifications.

:keyword:`while`
   The optional :keyword:`else` clause is not supported.


.. _conv-subset-builtin:

Supported built-in functions
----------------------------

The following is a list of the built-in functions that are supported by the
Verilog converter.

:func:`bool`
   This function can be used to typecast an object explictly to its boolean
   interpretation.

:func:`len`
   For :class:`Signal` and :class:`intbv` objects, function :func:`len` returns the
   bit width.

:func:`int`
   This function can be used to typecast an object explictly to its integer
   interpretation.


.. _conv-subset-exclude:

Excluding code from conversion
------------------------------

For some tasks, such as debugging, it may be useful to insert arbitratry Python
code that should not be converted.

The Verilog convertor supports this by ignoring all code that is embedded in a
``if __debug__`` test. The value of the ``__debug__`` variable is not taken into
account.


.. _conv-meth:

Methodology notes
=================


.. _conv-meth-sim:

Simulation
----------

In the Python philosophy, the run-time rules. The Python compiler doesn't
attempt to detect a lot of errors beyond syntax errors, which given Python's
ultra-dynamic nature would be an almost impossible task anyway. To verify a
Python program, one should run it, preferably using unit testing to verify each
feature.

The same philosophy should be used when converting a MyHDL description to
Verilog: make sure the simulation runs fine first. Although the converter checks
many things and attempts to issue clear error messages, there is no guarantee
that it does a meaningful job unless the simulation runs fine.


.. _conv-meth-conv:

Conversion output verification
------------------------------

It is always prudent to verify the converted Verilog output. To make this task
easier, the converter also generates a test bench that makes it possible to
simulate the Verilog design using the Verilog co-simulation interface. This
permits to verify the Verilog code with the same test bench used for the MyHDL
code. This is also how the Verilog converter development is being verified.


.. _conv-meth-assign:

Assignment issues
-----------------


.. _conv-meth-assign-python:

Name assignment in Python
^^^^^^^^^^^^^^^^^^^^^^^^^

Name assignment in Python is a different concept than in many other languages.
This point is very important for effective modeling in Python, and even more so
for synthesizable MyHDL code. Therefore, the issues are discussed here
explicitly.

Consider the following name assignments::

   a = 4
   a = ``a string''
   a = False

In many languages, the meaning would be that an existing variable *a* gets a
number of different values. In Python, such a concept of a variable doesn't
exist. Instead, assignment merely creates a new binding of a name to a certain
object, that replaces any previous binding. So in the example, the name *a* is
bound a  number of different objects in sequence.

The Verilog converter has to investigate name assignment and usage in MyHDL
code, and to map names to Verilog variables. To achieve that, it tries to infer
the type and possibly the bit width of each expression that is assigned to a
name.

Multiple assignments to the same name can be supported if it can be determined
that a consistent type and bit width is being used in the assignments. This can
be done for boolean expressions, numeric expressions, and enumeration type
literals. In Verilog, the corresponding name is mapped to a single bit ``reg``,
an ``integer``, or a ``reg`` with the appropriate width, respectively.

In other cases, a single assignment should be used when an object is created.
Subsequent value changes are then achieved by modification of an existing
object.  This technique should be used for :class:`Signal` and :class:`intbv`
objects.


.. _conv-meth-assign-signal:

Signal assignment
^^^^^^^^^^^^^^^^^

Signal assignment in MyHDL is implemented using attribute assignment to
attribute ``next``.  Value changes are thus modeled by modification of the
existing object. The converter investigates the :class:`Signal` object to infer
the type and bit width of the corresponding Verilog variable.


.. _conv-meth-assign-intbv:

:class:`intbv` objects
^^^^^^^^^^^^^^^^^^^^^^

Type :class:`intbv` is likely to be the workhorse for synthesizable modeling in
MyHDL. An :class:`intbv` instance behaves like a (mutable) integer whose
individual bits can be accessed and modified. Also, it is possible to constrain
its set of values. In addition to error checking, this makes it possible to
infer a bit width, which is required for implementation.

In Verilog, an :class:`intbv` instance will be mapped to a ``reg`` with an
appropriate width. As noted before, it is not possible to modify its value using
name assignment. In the following, we will show how it can be done instead.
Consider::

   a = intbv(0)[8:]

This is an :class:`intbv` object with initial value ``0`` and bit width 8. The
change its value to ``5``, we can use slice assignment::

   a[8:] = 5

The same can be achieved by leaving the bit width unspecified,  which has the
meaning to change "all" bits::

   a[:] = 5

Often the new value will depend on the old one. For example, to increment an
:class:`intbv` with the technique above::

   a[:] = a + 1

Python also provides *augmented* assignment operators, which can be used to
implement in-place operations. These are supported on :class:`intbv` objects and
by the converter, so that the increment can also be done as follows::

   a += 1


.. _conv-usage:

Converter usage
===============

We will demonstrate the conversion process by showing some examples.


.. _conv-usage-seq:

A small sequential design
-------------------------

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
----------------------------

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
---------------------

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
---------------------------------------

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
-------------

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
-------------

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

User-defined Verilog code
-------------------------

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


.. _conv-issues:

Known issues
============

Verilog integers are 32 bit wide
   Usually, Verilog integers are 32 bit wide. In contrast, Python is moving toward
   integers with undefined width. Python :class:`int`  and :class:`long` variables
   are mapped to Verilog integers; so for values wider than 32 bit this mapping is
   incorrect.

Synthesis pragmas are specified as Verilog comments.
   The recommended way to specify synthesis pragmas in Verilog is through attribute
   lists. However, the Icarus simulator doesn't support them for ``case``
   statements (to specify ``parallel_case`` and ``full_case`` pragmas). Therefore,
   the old but deprecated method of synthesis pragmas in Verilog comments is still
   used.

Inconsistent place of the sensitivity list inferred from ``always_comb``.
   The semantics of ``always_comb``, both in Verilog and MyHDL, is to have an
   implicit sensitivity list at the end of the code. However, this may not be
   synthesizable. Therefore, the inferred sensitivity list is put at the top of the
   corresponding ``always`` block. This may cause inconsistent behavior at the
   start of the simulation. The workaround is to create events at time 0.

Non-blocking assignments to task arguments don't work.
   Non-blocking (signal) assignments to task arguments don't work for an as yet
   unknown reason.

