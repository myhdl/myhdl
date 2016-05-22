.. currentmodule:: myhdl

.. _cosim:

**************************
Co-simulation with Verilog
**************************


.. _cosim-intro:

Introduction
============

One of the most exciting possibilities of MyHDL\ is to use it as a hardware
verification language (HVL). A HVL is a language used to write test benches and
verification environments, and to control simulations.

Nowadays, it is generally acknowledged that HVLs should be equipped with modern
software techniques, such as object orientation. The reason is that verification
it the most complex and time-consuming task of the design process. Consequently,
every useful technique is welcome. Moreover, test benches are not required to be
implementable. Therefore, unlike with synthesizable code, there are no
constraints on creativity.

Technically, verification of a design implemented in another language requires
co-simulation. MyHDL is  enabled for co-simulation with any HDL simulator that
has a procedural language interface (PLI). The MyHDL\ side is designed to be
independent of a particular simulator, On the other hand, for each HDL simulator
a specific PLI module will have to be written in C. Currently, the MyHDL release
contains a PLI module for two Verilog simulators: Icarus and Cver.


.. _cosim-hdl:

The HDL side
============

To introduce co-simulation, we will continue to use the Gray encoder example
from the previous chapters. Suppose that we want to synthesize it and write it
in Verilog for that purpose. Clearly we would like to reuse our unit test
verification environment.

To start, let's recall how the Gray encoder in MyHDL looks like:

.. include-example:: bin2gray.py

To show the co-simulation flow, we don't need the Verilog implementation yet,
but only the interface.  Our Gray encoder in Verilog would have the following
interface::

   module bin2gray(B, G);

      parameter width = 8;
      input [width-1:0]  B;
      output [width-1:0] G;
      ....

To write a test bench, one creates a new module that instantiates the design
under test (DUT).  The test bench declares nets and regs (or signals in VHDL)
that are attached to the DUT, and to stimulus generators and response checkers.
In an all-HDL flow, the generators and checkers are written in the HDL itself,
but we will want to write them in MyHDL. To make the connection, we need to
declare which regs & nets are driven and read by the MyHDL\ simulator. For our
example, this is done as follows::

   module dut_bin2gray;

      reg [`width-1:0] B;
      wire [`width-1:0] G;

      initial begin
         $from_myhdl(B);
         $to_myhdl(G);
      end

      bin2gray dut (.B(B), .G(G));
      defparam dut.width = `width;

   endmodule

The ``$from_myhdl`` task call declares which regs are driven by MyHDL, and the
``$to_myhdl`` task call which regs & nets are read by it. These tasks take an
arbitrary number of arguments.  They are defined in a PLI module written in C
and made available in a simulator-dependent manner.  In Icarus Verilog, the
tasks are defined in a ``myhdl.vpi`` module that is compiled from C source code.


.. _cosim-myhdl:

The MyHDL side
==============

MyHDL supports co-simulation by a ``Cosimulation`` object.  A ``Cosimulation``
object must know how to run a HDL simulation. Therefore, the first argument to
its constructor is a command string to execute a simulation.

The way to generate and run an simulation executable is simulator dependent.
For example, in Icarus Verilog, a simulation executable for our example can be
obtained obtained by running the ``iverilog`` compiler as follows::

   % iverilog -o bin2gray -Dwidth=4 bin2gray.v dut_bin2gray.v

This generates a ``bin2gray`` executable for a parameter ``width`` of 4, by
compiling the contributing Verilog files.

The simulation itself is run by the ``vvp`` command::

   % vvp -m ./myhdl.vpi bin2gray

This runs the ``bin2gray`` simulation, and specifies to use the ``myhdl.vpi``
PLI module present in the current directory. (This is  just a command line usage
example; actually simulating with the ``myhdl.vpi`` module is only meaningful
from a ``Cosimulation`` object.)

We can use a ``Cosimulation`` object to provide a HDL version of a design to the
MyHDL simulator. Instead of a generator function, we write a function that
returns a ``Cosimulation`` object. For our example and the Icarus Verilog
simulator, this is done as follows::

   import os

   from myhdl import Cosimulation

   cmd = "iverilog -o bin2gray.o -Dwidth=%s " + \
         "../../test/verilog/bin2gray.v " + \
         "../../test/verilog/dut_bin2gray.v "

   def bin2gray(B, G):
       width = len(B)
       os.system(cmd % width)
       return Cosimulation("vvp -m ../myhdl.vpi bin2gray.o", B=B, G=G)

After the executable command argument, the ``Cosimulation`` constructor takes an
arbitrary number of keyword arguments. Those arguments make the link between
MyHDL Signals and HDL nets, regs, or signals, by named association. The keyword
is the name of an argument in a ``$to_myhdl`` or ``$from_myhdl`` call; the
argument is a MyHDL Signal.

With all this in place, we can now use the existing unit test to verify the
Verilog implementation. Note that we kept the same name and parameters for the
the ``bin2gray`` function: all we need to do is to provide this alternative
definition to the existing unit test.

Let's try it on the Verilog design::

  module bin2gray(B, G);

     parameter width = 8;
     input [width-1:0]  B;
     output [width-1:0] G;

     assign G = (B >> 1) ^ B;

  endmodule // bin2gray

When we run our unit tests, we get::

   % python test_gray.py
   testSingleBitChange (test_gray_properties.TestGrayCodeProperties)
   Check that only one bit changes in successive codewords. ... ok
   testUniqueCodeWords (test_gray_properties.TestGrayCodeProperties)
   Check that all codewords occur exactly once. ... ok
   testOriginalGrayCode (test_gray_original.TestOriginalGrayCode)
   Check that the code is an original Gray code. ... ok

   ----------------------------------------------------------------------
   Ran 3 tests in 0.706s

   OK

.. _cosim-restr:

Restrictions
============

In the ideal case, it should be possible to simulate any HDL description
seamlessly with MyHDL. Moreover the communicating signals at each side should
act transparently as a single one, enabling fully race free operation.

For various reasons, it may not be possible or desirable to achieve full
generality. As anyone that has developed applications with the Verilog PLI can
testify, the restrictions in a particular simulator, and the  differences over
various simulators, can be quite  frustrating. Moreover, full generality may
require a disproportionate amount of development work compared to a slightly
less general solution that may be sufficient for the target application.

Consequently, I have tried to achieve a solution which is simple enough so that
one can reasonably  expect that any PLI-enabled simulator can support it, and
that is relatively easy to verify and maintain. At the same time, the solution
is sufficiently general  to cover the target application space.

The result is a compromise that places certain restrictions on the HDL code. In
this section, these restrictions  are presented.


.. _cosim-pass:

Only passive HDL can be co-simulated
------------------------------------

The most important restriction of the MyHDL co-simulation solution is that only
"passive" HDL can be co-simulated.  This means that the HDL code should not
contain any statements with time delays. In other words, the MyHDL simulator
should be the master of time; in particular, any clock signal should be
generated at the MyHDL side.

At first this may seem like an important restriction, but if one considers the
target application for co-simulation, it probably isn't.

MyHDL supports co-simulation so that test benches for HDL designs can be written
in Python.  Let's consider the nature of the target HDL designs. For high-level,
behavioral models that are not intended for implementation, it should come as no
surprise that I would recommend to write them in MyHDL directly; that is one of
the goals of the MyHDL effort. Likewise, gate level designs with annotated
timing are not the target application: static timing analysis is a much better
verification method for such designs.

Rather, the targeted HDL designs are naturally models that are intended for
implementation, most likely through synthesis. As time delays are meaningless in
synthesizable code, the restriction is compatible with the target application.


.. _cosim-race:

Race sensitivity issues
-----------------------

In a typical RTL code, some events cause other events to occur in the same time
step. For example, when a clock signal triggers some signals may change in the
same time step. For race-free operation, an HDL must differentiate between such
events within a time step. This is done by the concept of "delta" cycles. In a
fully general, race free co-simulation, the co-simulators would communicate at
the level of delta cycles. However, in MyHDL co-simulation, this is not entirely
the case.

Delta cycles from the MyHDL simulator toward the HDL co-simulator are preserved.
However, in the opposite direction, they are not. The signals changes are only
returned to the MyHDL simulator after all delta cycles have been performed in
the HDL co-simulator.

What does this mean? Let's start with the good news. As explained in the
previous section, the concept behind MyHDL co-simulation implies that clocks are
generated at the MyHDL side.  *When using a MyHDL clock and its corresponding
HDL signal directly as a clock, co-simulation is race free.* In other words, the
case that most closely reflects the MyHDL co-simulation approach, is race free.

The situation is different when you want to use a signal driven by the HDL (and
the corresponding MyHDL signal) as a clock.  Communication triggered by such a
clock is not race free. The solution is to treat such an interface as a chip
interface instead of an RTL interface.  For example, when data is triggered at
positive clock edges, it can safely be sampled at negative clock edges.
Alternatively, the MyHDL data signals can be declared with a delay value, so
that they are guaranteed to change after the clock edge.


.. _cosim-impl:

Implementation notes
====================

   This section requires some knowledge of PLI terminology.


Enabling a simulator for co-simulation requires a PLI module written in C. In
Verilog, the PLI is part of the "standard".  However, different simulators
implement different versions and portions of the standard. Worse yet, the
behavior of certain PLI callbacks is not defined on some essential points.  As a
result, one should plan to write or at least customize a specific PLI module for
any simulator. The release contains a PLI module for the open source Icarus and
Cver simulators.

This section documents the current approach and status of the PLI module
implementation and some reflections on future implementations.


.. _cosim-icarus:

Icarus Verilog
--------------


.. _cosim-icarus-delta:

Delta cycle implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^

To make co-simulation work, a specific type of PLI callback is needed. The
callback should be run when all pending events have been processed, while
allowing the creation of new events in the current time step (e.g. by the MyHDL
simulator).  In some Verilog simulators, the ``cbReadWriteSync`` callback does
exactly that. However, in others, including Icarus, it does not. The callback's
behavior is not fully standardized; some simulators run the callback before non-
blocking assignment events have been processed.

Consequently, I had to look for a workaround. One half of the solution is to use
the ``cbReadOnlySync`` callback.  This callback runs after all pending events
have been processed.  However, it does not permit to create new events in the
current time step.  The second half of the solution is to map MyHDL delta cycles
onto real Verilog time steps.  Note that fortunately I had some freedom here
because of the restriction that only passive HDL code can be co-simulated.

I chose to make the time granularity in the Verilog simulator a 1000 times finer
than in the MyHDL simulator. For each MyHDL time step, 1000 Verilog time steps
are available for MyHDL delta cycles. In practice, only a few delta cycles per
time step should be needed. Exceeding this limit almost certainly indicates a
design error; the limit is checked at run-time. The factor 1000 also makes it
easy to distinguish "real" time from delta cycle time when printing out the
Verilog time.


.. _cosim-icarus-pass:

Passive Verilog check
^^^^^^^^^^^^^^^^^^^^^

As explained before, co-simulated Verilog should not contain delay statements.
Ideally, there should be a run-time check to flag non-compliant code. However,
there is currently no such check in the Icarus module.

The check can be written using the ``cbNextSimTime`` VPI callback in Verilog.
However, Icarus 0.7 doesn't support this callback. In the meantime, support for
it has been added to the Icarus development branch.  When Icarus 0.8 is
released, a check will be added.

In the mean time, just don't do this. It may appear to "work" but it really
won't as events will be missed over the co-simulation interface.


.. _cosim-cver:

Cver
----

MyHDL co-simulation is supported with the open source Verilog simulator Cver.
The PLI module is based on the one for Icarus and basically has the same
functionality. Only some cosmetic modifications were required.


.. _cosim-impl-verilog:

Other Verilog simulators
------------------------

The Icarus module is written with VPI calls, which are provided by the most
recent generation of the Verilog PLI. Some simulators may only support TF/ACC
calls, requiring a complete redesign of the interface module.

If the simulator supports VPI, the Icarus module should be reusable to a large
extent. However, it may be possible to improve on it.  The workaround to support
delta cycles described in Section :ref:`cosim-icarus-delta` may not be
necessary. In some simulators, the ``cbReadWriteSync`` callback occurs after all
events (including non-blocking assignments) have been processed. In that case,
the functionality can be supported without a finer time granularity in the
Verilog simulator.

There are also Verilog standardization efforts underway to resolve the ambiguity
of the ``cbReadWriteSync`` callback. The solution will be to introduce new, well
defined callbacks. From reading some proposals, I conclude that the
``cbEndOfSimTime`` callback would provide the required functionality.

The MyHDL project currently has no access to commercial Verilog simulators, so
progress in co-simulation support depends on external interest and
participation. Users have reported that they are using MyHDL co-simulation with
the simulators from Aldec and Modelsim.


.. _cosim-impl-syscalls:

Interrupted system calls
------------------------

The PLI module uses ``read`` and ``write`` system calls to communicate between
the co-simulators. The implementation assumes that these calls are restarted
automatically by the operating system when interrupted. This is apparently what
happens on the Linux box on which MyHDL is developed.

It is known how non-restarted interrupted system calls should be handled, but
currently such code cannot be tested on the MyHDL development platform. Also, it
is not clear whether this is still a relevant issue with modern operating
systems. Therefore, this issue has not been addressed at this moment. However,
assertions have been included that should trigger when this situation occurs.

Whenever an assertion fires in the PLI module, please report it.  The same holds
for Python exceptions that cannot be easily explained.


.. _cosim-impl-vhdl:

What about VHDL?
----------------

It would be nice to have an interface to VHDL simulators such as the Modelsim
VHDL simulator. Let us summarize the requirements to accomplish that:

* We need a procedural interface to the internals of the simulator.
* The procedural interface should be a widely used industry standard so that we
  can reuse the work in several simulators.
* MyHDL is an open-source project and therefore there should be also be an open-source
  simulator that implements the procedural interface.


``vpi`` for Verilog matches these requirements. It is a widely used standard
and is supported by the open-source Verilog simulators Icarus and cver.

However, for VHDL the situation is different. While there exists a standard
called ``vhpi``, it  much less popular than ``vpi``. Also, to our knowledge
there is only one credible open source VHDL simulator (GHDL) and it is unclear
whether it has ``vhpi`` capabilities that are powerful
enough for MyHDL's purposes.


Consequently, the development of co-simulation for VHDL is currently on
hold. For some applications, there is an alternative: see :ref:`conv-testbench`.
