.. currentmodule:: myhdl


.. _model-structure:

*******************
Structural modeling
*******************

.. index:: single: modeling; structural

Introduction
============

Hardware descriptions need to support the concepts of module instantiation and
hierarchy.  In MyHDL, an instance is recursively defined as being either a
sequence of instances, or a generator. Hierarchy is modeled by defining
instances in a higher-level function, and returning them.  The following is a
schematic example of the basic case. ::

   from myhdl import block

   @block
   def top(...):
       ...
       instance_1 = module_1(...)
       instance_2 = module_2(...)
       ...
       instance_n = module_n(...)
       ...
       return instance_1, instance_2, ... , instance_n

Note that MyHDL uses conventional procedural techniques for modeling structure.
This makes it straightforward to model more complex cases.


.. _model-conf:

Conditional instantiation
=========================

.. index:: single: conditional instantiation

To model conditional instantiation, we can select the returned instance under
parameter control. For example::

   from myhdl import block

   SLOW, MEDIUM, FAST = range(3)

   @block
   def top(..., speed=SLOW):
       ...
       def slowAndSmall():
          ...
       ...
       def fastAndLarge():
          ...
       if speed == SLOW:
           return slowAndSmall()
       elif speed == FAST:
           return fastAndLarge()
       else:
           raise NotImplementedError


.. _model-instarray:

Lists of instances and signals
------------------------------

.. index:: single: lists of instances and signals

Python lists are easy to create. We can use them to model lists of instances.

Suppose we have a top module that instantiates a single ``channel`` submodule,
as follows::

   from myhdl import block, Signal

   @block
   def top(...):

       din = Signal(0)
       dout = Signal(0)
       clk = Signal(bool(0))
       reset = Signal(bool(0))

       channel_inst = channel(dout, din, clk, reset)

       return channel_inst

If we wanted to support an arbitrary number of channels, we can use lists of
signals and a list of instances, as follows::

   from myhdl import block, Signal

   @block
   def top(..., n=8):

       din = [Signal(0) for i in range(n)]
       dout = [Signal(0) for in range(n)]
       clk = Signal(bool(0))
       reset = Signal(bool(0))
       channel_inst = [None for i in range(n)]

       for i in range(n):
           channel_inst[i] = channel(dout[i], din[i], clk, reset)

       return channel_inst

.. _model-shadow-signals:

Converting between lists of signals and bit vectors
===================================================

Compared to HDLs such as VHDL and Verilog, MyHDL signals are less
flexible for structural modeling. For example, slicing a signal
returns a slice of the current value. For behavioral code, this is
just fine. However, it implies that you cannot use such as slice in
structural descriptions. In other words, a signal slice cannot be used
as a signal.

In MyHDL, you can address such cases by a concept called
shadow signals. A shadow signal is constructed out of
other signals and follows their value changes automatically.
For example, a :class:`_SliceSignal` follows the value of
an index or a slice from another signal.  Likewise,
A :class:`ConcatSignal` follows the
values of a number of signals as a concatenation.

As an example, suppose we have a system with N requesters that
need arbitration. Each requester has a ``request`` output
and a ``grant`` input. To connect them in the system, we can
use list of signals. For example, a list of request signals
can be constructed as follows::

    request_list = [Signal(bool()) for i in range(M)]

Suppose that an arbiter module is available that is
instantiated as follows::

    arb = arbiter(grant_vector, request_vector, clock, reset)

The ``request_vector`` input is a bit vector that can have
any of its bits asserted. The ``grant_vector`` is an output
bit vector with just a single bit asserted, or none.
Such a module is typically based on bit vectors because
they are easy to process in RTL code. In MyHDL, a bit vector
is modeled using the :class:`intbv` type.

We need a way to "connect" the list of signals to the
bit vector and vice versa. Of course, we can do this with explicit
code, but shadow signals can do this automatically. For
example, we can construct a ``request_vector`` as a
:class:`ConcatSignal` object::

    request_vector = ConcatSignal(*reversed(request_list)

Note that we reverse the list first. This is done because the index range
of lists is the inverse of the range of :class:`intbv` bit vectors.
By reversing, the indices correspond to the same bit.

The inverse problem exist for the ``grant_vector``. It would be defined as follows::

    grant_vector = Signal(intbv(0)[M:])

To construct a list of signals that are connected automatically to the
bit vector, we can use the :class:`Signal` call interface to construct
:class:`_SliceSignal` objects::

    grant_list = [grant_vector(i) for i in range(M)]

Note the round brackets used for this type of slicing. Also, it may not be
necessary to construct this list explicitly. You can simply use
``grant_vector(i)`` in an instantiation.

To decide when to use normal or shadow signals, consider the data
flow. Use normal signals to connect to *outputs*. Use shadow signals to
transform these signals so that they can be used as *inputs*.


.. _model-infer-instlist:

Inferring the list of instances
===============================

In MyHDL, instances have to be returned explicitly by a top level function. It
may be convenient to assemble  the list of instances automatically. For this
purpose, MyHDL  provides the function :func:`instances`. Using the first example
in this section, it is used as follows::

   from myhdl import block, instances

   @block
   def top(...):
       ...
       instance_1 = module_1(...)
       instance_2 = module_2(...)
       ...
       instance_n = module_n(...)
       ...
       return instances()

Function :func:`instances` uses introspection to inspect the type of the local
variables defined by the calling function. All variables that comply with the
definition of an instance are assembled in a list, and that list is returned.
