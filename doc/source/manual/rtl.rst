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
:dfn:`Synthesis` refers to the process by which an HDL description
is automatically compiled into an implementation for an ASIC or FPGA.
This chapter describes how MyHDL supports it.


.. _model-comb:

Combinatorial logic
===================

.. index:: single: combinatorial logic


.. _model-comb-templ:

Template
--------


Combinatorial logic is described with a code pattern as follows::

   from myhdl import block, always_comb

   @block
   def top(<parameters>):
       ...
       @always_comb
       def comb_logic():
           <functional code>
       ...
       return comb_logic, ...

The :func:`always_comb` decorator describes combinatorial logic. The name refers
to a similar construct in SystemVerilog. The decorated function is a local
function that specifies what happens when one of the input signals of the logic
changes.  The :func:`always_comb` decorator infers the input signals
automatically. It returns a generator that is sensitive to all inputs, and that
executes the function whenever an input changes.

.. _model-comb-ex:

Example
-------

The following is an example of a combinatorial multiplexer

.. include-example:: mux.py


To verify it, we will simulate the logic with some random patterns. The
``random`` module in Python's standard library comes in handy for such purposes.
The function ``randrange(n)`` returns a random natural integer smaller than *n*.
It is used in the test bench code to produce random input values.

.. include-example:: test_mux.py

It is often useful to keep the random values reproducible. This can be
accomplished by providing a seed value as in the code. The run produces the
following output:

.. run-example:: test_mux.py

.. _model-seq:

Sequential logic
================

.. index:: single: sequential logic

.. _model-seq-templ:

Template
--------

Sequential RTL models are sensitive to a clock edge. In addition, they may be
sensitive to a reset signal.  The :func:`always_seq` decorator supports this
model directly::

   from myhdl import block, always_seq

   @instance
   def top(<parameters>, clock, ..., reset, ...):
       ...
       @always_seq(clock.posedge, reset=reset)
       def seq_logic():
           <functional code>
       ...
       return seq_logic, ...

The :func:`always_seq` decorator automatically infers the reset
functionality.  It detects which signals need to be reset, and uses their
initial values as the reset values. The reset signal itself needs to be
specified as a :class:`ResetSignal` object. For example::

    reset = ResetSignal(0, active=0, async=True)

The first parameter specifies the initial value. The *active* parameter
specifies the value on which the reset is active, and the *async*
parameter specifies whether it is an asychronous (``True``) or a
synchronous (``False``) reset. If no reset is needed, you can assign
``None`` to the *reset* parameter in the :func:`always_seq` parameter.

.. _model-seq-ex:

Example
-------

The following code is a description of an incrementer with enable, and an
asynchronous reset.

.. include-example:: inc.py

For the test bench, we will use an independent clock generator, stimulus
generator, and monitor. After applying enough stimulus patterns, we can raise
the :func:`StopSimulation()` exception to stop the simulation run. The test bench for
a small incrementer and a small number of patterns is a follows

.. include-example:: test_inc.py

The simulation produces the following output

.. run-example:: test_inc.py

.. _mode-seq-templ-alt:

Alternative template
--------------------

The template with the :func:`always_seq` decorator is convenient
as it infers the reset functionality automatically. Alternatively,
you can use a more explicit template as follows::

    from myhdl import block, always

    @block
    def top(<parameters>, clock, ..., reset, ...):
        ...
        @always(clock.posedge, reset.negedge)
        def seq_logic():
           if not reset:
               <reset code>
           else:
               <functional code>

        return seq_logic,...

With this template, the reset values have to be specified
explicitly.

.. _model-fsm:

Finite State Machine modeling
=============================

.. index:: single: modeling; Finite State Machine

Finite State Machine (FSM) modeling is very common in RTL design and therefore
deserves special attention.

For code clarity, the state values are typically represented by a set of
identifiers. A standard Python idiom for this purpose is to assign a range of
integers to a tuple of identifiers, like so


.. doctest::

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
attributes of the type. For example


.. doctest::

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
coded as follows

.. include-example:: fsm.py

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
enabled, is shown below:

.. include-example:: test_fsm.py

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
