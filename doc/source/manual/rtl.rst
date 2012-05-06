.. currentmodule:: myhdl


.. _model-rtl:

************
RTL modeling
************

Introduction
============

.. index:: single: modeling; RTL style

RTL (Register Transfer Level) is a modeling abstraction level that
is typically used to write synthesizable models.
This chapter describes how MyHDL supports it.


.. _model-comb:

Combinatorial logic
===================

.. index:: single: combinatorial logic


.. _model-comb-templ:

Template
--------

Combinatorial logic is described with a code pattern as follows::

   def top(<parameters>):
       ...
       @always_comb
       def combLogic():
           <functional code>
       ...
       return combLogic, ...

The :func:`always_comb` decorator describes combinatorial logic.  [#]_. The
decorated function is a local function that specifies what happens when one of
the input signals of the logic changes.  The :func:`always_comb` decorator
infers the input signals automatically. It returns a generator that is sensitive
to all inputs, and that executes the function whenever an input changes.


.. _model-comb-ex:

Example
-------

The following is an example of a combinatorial multiplexer::

   from myhdl import Signal, Simulation, delay, always_comb

   def Mux(z, a, b, sel):

       """ Multiplexer.

       z -- mux output
       a, b -- data inputs
       sel -- control input: select a if asserted, otherwise b

       """

       @always_comb
       def muxLogic():
           if sel == 1:
               z.next = a
           else:
               z.next = b

       return muxLogic

To verify it, we will simulate the logic with some random patterns. The
``random`` module in Python's standard library comes in handy for such purposes.
The function ``randrange(n)`` returns a random natural integer smaller than *n*.
It is used in the test bench code to produce random input values::

   from random import randrange

   z, a, b, sel = [Signal(0) for i in range(4)]

   mux_1 = Mux(z, a, b, sel)

   def test():
       print "z a b sel"
       for i in range(8):
           a.next, b.next, sel.next = randrange(8), randrange(8), randrange(2)
           yield delay(10)
           print "%s %s %s %s" % (z, a, b, sel)

   test_1 = test()

   sim = Simulation(mux_1, test_1)
   sim.run()    

Because of the randomness, the simulation output varies between runs  [#]_. One
particular run produced the following output::

   % python mux.py
   z a b sel
   6 6 1 1
   7 7 1 1
   7 3 7 0
   1 2 1 0
   7 7 5 1
   4 7 4 0
   4 0 4 0
   3 3 5 1
   StopSimulation: No more events


.. _model-seq:

Sequential logic
================

.. index:: single: sequential logic


.. _model-seq-templ:

Template
--------

Sequential RTL models are sensitive to a clock edge. In addition, they may be
sensitive to a reset signal. We will describe one of the most common patterns: a
template with a rising clock edge and an asynchronous reset signal. Other
templates are similar. ::

   def top(<parameters>, clock, ..., reset, ...):
       ...
       @always(clock.posedge, reset.negedge)
       def seqLogic():
           if reset == <active level>:
               <reset code>
           else:
               <functional code>
       ...
       return seqLogic, ...


.. _model-seq-ex:

Example
-------

The following code is a description of an incrementer with enable, and an
asynchronous reset. ::

   from random import randrange
   from myhdl import *

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

For the test bench, we will use an independent clock generator, stimulus
generator, and monitor. After applying enough stimulus patterns, we can raise
the ``StopSimulation`` exception to stop the simulation run. The test bench for
a small incrementer and a small number of patterns is a follows::

   def testbench():
       count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

       inc_1 = Inc(count, enable, clock, reset, n=4)

       HALF_PERIOD = delay(10)

       @always(HALF_PERIOD)
       def clockGen():
           clock.next = not clock

       @instance
       def stimulus():
           reset.next = ACTIVE_LOW
           yield clock.negedge
           reset.next = INACTIVE_HIGH
           for i in range(12):
               enable.next = min(1, randrange(3))
               yield clock.negedge
           raise StopSimulation

       @instance
       def monitor():
           print "enable  count"
           yield reset.posedge
           while 1:
               yield clock.posedge
               yield delay(1)
               print "   %s      %s" % (enable, count)

       return clockGen, stimulus, inc_1, monitor


   tb = testbench()

   def main():
       Simulation(tb).run()

The simulation produces the following output::

   % python inc.py
   enable  count
      0      0
      1      1
      0      1
      1      2
      1      3
      1      0
      0      0
      1      1
      0      1
      0      1
      0      1
      1      2
   StopSimulation


.. _model-fsm:

Finite State Machine modeling
=============================

.. index:: single: modeling; Finite State Machine

Finite State Machine (FSM) modeling is very common in RTL design and therefore
deserves special attention.

For code clarity, the state values are typically represented by a set of
identifiers. A standard Python idiom for this purpose is to assign a range of
integers to a tuple of identifiers, like so::

   >>> SEARCH, CONFIRM, SYNC = range(3)
   >>> CONFIRM
   1

However, this technique has some drawbacks. Though it is clearly the intention
that the identifiers belong together, this information is lost as soon as they
are defined. Also, the identifiers evaluate to integers, whereas a string
representation of the identifiers would be preferable. To solve these issues, we
need an *enumeration type*.

.. index:: single: enum(); example usage

MyHDL supports enumeration types by providing a function :func:`enum`.  The
arguments to :func:`enum` are the string representations of the identifiers, and
its return value is an enumeration type. The identifiers are available as
attributes of the type. For example::

   >>> from myhdl import enum
   >>> t_State = enum('SEARCH', 'CONFIRM', 'SYNC')
   >>> t_State
   <Enum: SEARCH, CONFIRM, SYNC>
   >>> t_State.CONFIRM
   CONFIRM

We can use this type to construct a state signal as follows::

   state = Signal(t_State.SEARCH)

As an example, we will use a framing controller FSM.  It is an imaginary
example, but similar control structures are often found in telecommunication
applications. Suppose that we need to find the Start Of Frame (SOF) position of
an incoming frame of bytes. A sync pattern detector continuously looks for a
framing pattern and indicates it to the FSM with a ``syncFlag`` signal. When
found, the FSM moves from the initial ``SEARCH`` state to the ``CONFIRM`` state.
When the ``syncFlag`` is confirmed on the expected position, the FSM declares
``SYNC``, otherwise it falls back to the ``SEARCH`` state.  This FSM can be
coded as follows::

   from myhdl import *

   ACTIVE_LOW = 0
   FRAME_SIZE = 8
   t_State = enum('SEARCH', 'CONFIRM', 'SYNC')

   def FramerCtrl(SOF, state, syncFlag, clk, reset_n):

       """ Framing control FSM.

       SOF -- start-of-frame output bit
       state -- FramerState output
       syncFlag -- sync pattern found indication input
       clk -- clock input
       reset_n -- active low reset

       """

       index = Signal(0) # position in frame

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

.. index:: single: waveform viewing

At this point, we will use the example to demonstrate the MyHDL support for
waveform viewing. During simulation, signal changes can be written to a VCD
output file.  The VCD file can then be loaded and viewed in a waveform viewer
tool such as :program:`gtkwave`.

.. % 

The user interface of this feature consists of a single function,
:func:`traceSignals`.  To explain how it works, recall that in MyHDL, an
instance is created by assigning the result of a function call to an instance
name. For example::

   tb_fsm = testbench()

To enable VCD tracing, the instance should be created as follows instead::

   tb_fsm = traceSignals(testbench)

Note that the first argument of :func:`traceSignals` consists of the uncalled
function. By calling the function under its control, :func:`traceSignals`
gathers information about the hierarchy and the signals to be traced. In
addition to a function argument, :func:`traceSignals` accepts an arbitrary
number of non-keyword and keyword arguments that will be passed to the function
call.

A small test bench for our framing controller example, with signal tracing
enabled, is shown below::

   def testbench():

       SOF = Signal(bool(0))
       syncFlag = Signal(bool(0))
       clk = Signal(bool(0))
       reset_n = Signal(bool(1))
       state = Signal(t_State.SEARCH)

       framectrl = FramerCtrl(SOF, state, syncFlag, clk, reset_n)

       @always(delay(10))
       def clkgen():
           clk.next = not clk

       @instance
       def stimulus():
           for i in range(3):
               yield clk.posedge
           for n in (12, 8, 8, 4):
               syncFlag.next = 1
               yield clk.posedge
               syncFlag.next = 0
               for i in range(n-1):
                   yield clk.posedge
           raise StopSimulation

       return framectrl, clkgen, stimulus


   tb_fsm = traceSignals(testbench)
   sim = Simulation(tb_fsm)
   sim.run()

When we run the test bench, it generates a VCD file called
:file:`testbench.vcd`. When we load this file into :program:`gtkwave`, we can
view the waveforms:

.. image:: tbfsm.png

Signals are dumped in a suitable format. This format is inferred at the
:class:`Signal` construction time, from the type of the initial value. In
particular, :class:`bool` signals are dumped as single bits. (This only works
starting with Python 2.3, when :class:`bool` has become a separate type).
Likewise, :class:`intbv` signals with a defined bit width are dumped as bit
vectors. To support the general case, other types of signals are dumped as a
string representation, as returned by the standard :func:`str` function.

.. warning::

   Support for literal string representations is not part of the VCD standard. It
   is specific to :program:`gtkwave`. To generate a standard VCD file, you need to
   use signals with a defined bit width only.


.. rubric:: Footnotes

.. [#] The name :func:`always_comb` refers to a construct with similar semantics in
   SystemVerilog.

.. [#] It also possible to have a reproducible random output, by explicitly providing a
   seed value. See the documentation of the ``random`` module.


