.. currentmodule:: myhdl


.. _intro:

*********************
Introduction to MyHDL
*********************


.. _intro-basic:

A basic MyHDL simulation
========================

We will introduce MyHDL with a classic ``Hello World`` style example. All
example code can be found in the distribution directory under
:file:`example/manual/`.  Here are the contents of a MyHDL simulation script
called :file:`hello1.py`::

   from myhdl import Signal, delay, always, now, Simulation

   def HelloWorld():

       interval = delay(10)

       @always(interval)
       def sayHello():
           print "%s Hello World!" % now()

       return sayHello


   inst = HelloWorld()
   sim = Simulation(inst)
   sim.run(30)

When we run this simulation, we get the following output::

   % python hello1.py
   10 Hello World!
   20 Hello World!
   30 Hello World!
   _SuspendSimulation: Simulated 30 timesteps

The first line of the script imports a number of objects from the ``myhdl``
package. In Python we can only use identifiers that are literally defined in the
source file   [#]_.

Then, we define a function called :func:`HelloWorld`. In MyHDL, classic
functions are used to model hardware modules. In particular, the parameter list
is used to define the interface. In this first example, the interface is empty.

.. index:: single: decorator; always

Inside the top level function we declare a local function called
:func:`sayHello` that defines the desired behavior. This function is decorated
with an :func:`always` decorator that has a delay  object as its parameter.  The
meaning is that the function will be executed whenever the specified delay
interval has expired.

Behind the curtains, the :func:`always` decorator creates a Python *generator*
and reuses the name of the decorated function for it. Generators are the
fundamental objects in MyHDL, and we will say much more about them further on.

Finally, the top level function returns the local generator. This is the
simplest case of the basic MyHDL code pattern to define the contents of a
hardware module. We will describe the general case further on.

In MyHDL, we create an *instance* of a hardware module by calling the
corresponding function. In the example, variable ``inst`` refers to an instance
of :func:`HelloWorld`.  To simulate the instance, we pass it as an argument to a
:class:`Simulation` object constructor.  We then run the simulation for the
desired amount of timesteps.


.. _intro-conc:

Signals, ports, and concurrency
===============================

In the previous section, we simulated a design with a single generator and no
concurrency. Real hardware descriptions are typically
massively concurrent. MyHDL supports this by allowing an arbitrary number of
concurrently running generators.

With concurrency comes the problem of deterministic communication. Hardware
languages use special objects to support deterministic communication between
concurrent code. In particular, MyHDL  has a :class:`Signal` object which is
roughly modeled after VHDL signals.

We will demonstrate signals and concurrency by extending and modifying our first
example. We define two hardware modules, one that drives a clock signal, and one
that is sensitive to a positive edge on a clock signal::

   from myhdl import Signal, delay, always, now, Simulation


   def ClkDriver(clk):

       halfPeriod = delay(10)

       @always(halfPeriod)
       def driveClk():
           clk.next = not clk

       return driveClk


   def HelloWorld(clk):

       @always(clk.posedge)
       def sayHello():
           print "%s Hello World!" % now()

       return sayHello


   clk = Signal(0)
   clkdriver_inst = ClkDriver(clk)
   hello_inst = HelloWorld(clk)
   sim = Simulation(clkdriver_inst, hello_inst)
   sim.run(50)

.. index::
   single: VHDL; signal assignment
   single: Verilog; non-blocking assignment

The clock driver function :func:`ClkDriver` has a clock signal as its parameter.
This is how a *port* is modeled in MyHDL. The function defines a generator that
continuously toggles a clock signal after a certain delay. A new value of a
signal is specified by assigning to its ``next`` attribute. This is the MyHDL
equivalent of  the VHDL signal assignment and the  Verilog non-blocking
assignment.

.. index:: single: wait; for a rising edge

The :func:`HelloWorld` function is modified from the first example. It now also
takes a clock signal as parameter. Its generator is made sensitive to a rising
edge of the clock signal. This is specified by the ``posedge`` attribute of a
signal. The edge specifier is the argument of the ``always`` decorator. As a
result, the decorated function will be executed on every rising clock edge.

The ``clk`` signal is constructed with an initial value ``0``. When creating an
instance of each  hardware module, the same clock signal is passed as the
argument. The result is that the instances are now connected through the clock
signal. The :class:`Simulation` object is constructed with the two instances.

When we run the simulation, we get::

   % python hello2.py
   10 Hello World!
   30 Hello World!
   50 Hello World!
   _SuspendSimulation: Simulated 50 timesteps


.. _intro-hier:

Parameters and hierarchy
========================

We have seen that MyHDL uses functions to model hardware modules. We have also
seen that ports are modeled by using signals as parameters. To make designs
reusable we will also want to use other objects as parameters. For example, we
can change the clock generator function to make it more general and reusable, by
making the clock period parametrizable, as follows::

   from myhdl import Signal, delay, instance, always, now, Simulation

   def ClkDriver(clk, period=20):

       lowTime = int(period/2)
       highTime = period - lowTime

       @instance
       def driveClk():
           while True:
               yield delay(lowTime)
               clk.next = 1
               yield delay(highTime)
               clk.next = 0

       return driveClk

In addition to the clock signal, the clock period is a parameter, with a default
value of ``20``.

.. index:: single: decorator; instance

As the low time of the clock may differ from the high time in case of an odd
period, we cannot use the :func:`always` decorator with a single delay value
anymore. Instead, the :func:`driveClk` function is now a generator function with
an explicit definition of the desired behavior. It is decorated with the
:func:`instance` decorator.  You can see that :func:`driveClk` is a generator
function because it contains ``yield`` statements.

When a generator function is called, it returns a generator object. This is
basically what the :func:`instance` decorator does. It is less sophisticated
than the :func:`always` decorator, but it can be used to create a generator from
any local generator function.

The ``yield`` statement is a general Python construct, but MyHDL uses it in a
dedicated way.  In MyHDL, it has a similar meaning as the wait statement in
VHDL: the statement suspends execution of a generator, and its clauses specify
the conditions on which the generator should wait before resuming. In this case,
the generator waits for a certain delay.

Note that to make sure that the generator runs "forever", we wrap its behavior
in a ``while True`` loop.

Similarly, we can define a general :func:`Hello` function as follows::

   def Hello(clk, to="World!"):

       @always(clk.posedge)
       def sayHello():
           print "%s Hello %s" % (now(), to)

       return sayHello

.. index:: single: instance; defined

We can create any number of instances by calling the functions with the
appropriate parameters. Hierarchy can be modeled by defining the instances in a
higher-level function, and returning them. This pattern can be repeated for an
arbitrary number of hierarchical levels. Consequently, the general definition of
a MyHDL instance is recursive: an instance is either a sequence of instances, or
a generator.


As an example, we will create a higher-level function with four instances of the
lower-level functions, and simulate it::

   def greetings():

       clk1 = Signal(0)
       clk2 = Signal(0)

       clkdriver_1 = ClkDriver(clk1) # positional and default association
       clkdriver_2 = ClkDriver(clk=clk2, period=19) # named association 
       hello_1 = Hello(clk=clk1) # named and default association
       hello_2 = Hello(to="MyHDL", clk=clk2) # named association

       return clkdriver_1, clkdriver_2, hello_1, hello_2


   inst = greetings()
   sim = Simulation(inst)
   sim.run(50)

As in standard Python, positional or named parameter association can be used in
instantiations, or a mix of both [#]_. All these styles are demonstrated in the
example above. Named association can be very useful if there are a lot of
parameters, as the argument order in the call does not matter in that case.

The simulation produces the following output::

   % python greetings.py
   9 Hello MyHDL
   10 Hello World!
   28 Hello MyHDL
   30 Hello World!
   47 Hello MyHDL
   50 Hello World!
   _SuspendSimulation: Simulated 50 timesteps

.. warning::

   Some commonly used terminology has different meanings in Python versus hardware
   design. Rather than artificially changing terminology, I think it's best to keep
   it and explicitly describing the differences.

   .. index:: single: module; in Python versus hardware design

   A :dfn:`module` in Python refers to all source code in a particular file. A
   module can be reused by other modules by importing. In hardware design, a module
   is  a reusable block of hardware with a well defined interface. It can be reused
   in  another module by :dfn:`instantiating` it.

   .. index:: single: instance; in Python versus hardware design

   An :dfn:`instance` in Python (and other object-oriented languages) refers to the
   object created by a class constructor. In hardware design, an instance is a
   particular incarnation of a hardware module.

   Normally, the meaning should be clear from the context. Occasionally, I may
   qualify terms  with the words "hardware" or "MyHDL" to  avoid ambiguity.


.. _intro-bit:

Bit oriented operations
=======================

.. _intro-intbv:

The :class:`intbv` class
------------------------


.. index:: single: intbv; basic usage

Hardware design involves dealing with bits and bit-oriented operations. The
standard Python type :class:`int` has most of the desired features, but lacks
support for indexing and slicing. For this reason, MyHDL provides the
:class:`intbv` class. The name was chosen to suggest an integer with bit vector
flavor.

:class:`intbv` works transparently with other integer-like types. Like
class :class:`int`, it provides access to the underlying two's complement
representation for bitwise operations. However, unlike :class:`int`, it is
a mutable type. This means that its value can be changed after object
creation, through methods and operators such as slice assignment.

:class:`intbv` supports the same operators as :class:`int` for arithmetic.
In addition, it provides a number of features to make it
suitable for hardware design. First, the range of allowed values can
be constrained. This makes it possible to check the value at run time
during simulation. Moreover, back end tools can determine the smallest
possible bit width for representing the object.
Secondly, it supports bit level operations by providing an indexing
and slicing interface.

:class:`intbv` objects are constructed in general as follows::

    intbv([val=None] [, min=None]  [, max=None])

*val* is the initial value. *min* and *max* can be used to constrain
the value. Following the Python conventions, *min* is inclusive, and
*max* is exclusive. Therefore, the allowed value range is *min* .. *max*-1.

Let's us look at some examples. First, an unconstrained :class:`intbv`
object is created as follows:

  >>> a = intbv(24)
  
.. index::  
    single: intbv; min
    single: intbv; max
    single: intbv; bit width

After object creation, *min* and *max* are available as attributes for
inspection. Also, the standard Python function :func:`len` can be used
to determine the bit width. If we inspect the previously created
object, we get::
  
  >>> print a.min
  None
  >>> print a.max
  None
  >>> print len(a)
  0

As the instantiation was unconstrained, the *min* and *max* attributes
are undefined. Likewise, the bit width is undefined, which is indicated
by a return value ``0``.

A constrained :class:`intbv` object is created as follows:

  >>> a = intbv(24, min=0, max=25)


Inspecting the object now gives::

  >>> a.min
  0
  >>> a.max
  25
  >>> len(a)
  5

We see that the allowed value range is 0 .. 24,  and that 5 bits are
required to represent the object.

Sometimes hardware engineers prefer to constrain an object by defining
its bit width directly, instead of the range of allowed values.
The following example shows how to do that::

  >>> a = intbv(24)[5:]

What actually happens here is that first an unconstrained :class:`intbv`
is created, which is then sliced. Slicing an :class:`intbv` returns a new
:class:`intbv` with the constraints set up appropriately. 
Inspecting the object now shows::

  >>> a.min
  0
  >>> a.max
  32
  >>> len(a)
  5


Note that the *max* attribute is 32, as with 5 bits it is
possible to represent the range 0 .. 31.
Creating an
:class:`intbv` this way has the disadvantage that only positive value
ranges can be specified. Slicing is described in more detail
in :ref:`intro-slicing`.

To summarize, there are two ways to constrain an :class:`intbv` object: by
defining its bit width, or by defining its value range. The bit
width method is more traditional in hardware design. However, there
are two reasons to use the range method instead: to represent
negative values as observed above, and for fine-grained control over the
value range.

Fine-grained control over the value range permits better error
checking, as there is no need for the *min* and *max* bounds
to be symmetric or powers of 2. In all cases, the bit width
is set appropriately to represent all values in 
the range. For example::


    >>> a = intbv(6, min=0, max=7)
    >>> len(a)
    3
    >>> a = intbv(6, min=-3, max=7)
    >>> len(a)
    4
    >>> a = intbv(6, min=-13, max=7)
    >>> len(a)
    5


.. _intro-indexing:

Bit indexing
------------

.. index:: single: bit indexing

As an example, we will consider the design of a Gray encoder. The following code
is a Gray encoder modeled in MyHDL::

   from myhdl import Signal, delay, Simulation, always_comb, instance, intbv, bin

   def bin2gray(B, G, width):
       """ Gray encoder.

       B -- input intbv signal, binary encoded
       G -- output intbv signal, gray encoded
       width -- bit width
       """

       @always_comb
       def logic():
           for i in range(width):
               G.next[i] = B[i+1] ^ B[i]

       return logic

This code introduces a few new concepts. The string in triple quotes at the
start of the function is a :dfn:`doc string`. This is standard Python practice
for structured documentation of code.

.. index::
   single: decorator; always_comb
   single: wait; for a signal value change
   single: combinatorial logic

Furthermore, we introduce a third decorator: :func:`always_comb`.  It is used
with a classic function and specifies that the  resulting generator should wait
for a value change on any input signal. This is typically used to describe
combinatorial logic. The :func:`always_comb` decorator automatically infers
which signals are used as inputs.

Finally, the code contains bit indexing operations and an exclusive-or operator
as required for a Gray encoder. By convention, the lsb of an :class:`intbv`
object has index ``0``.

To verify the Gray encoder, we write a test bench that prints input and output
for all possible input values::

   def testBench(width):

       B = Signal(intbv(0))
       G = Signal(intbv(0))

       dut = bin2gray(B, G, width)

       @instance
       def stimulus():
           for i in range(2**width):
               B.next = intbv(i)
               yield delay(10)
               print "B: " + bin(B, width) + "| G: " + bin(G, width)

       return dut, stimulus

We use the conversion function :func:`bin` to get a binary string representation of
the signal values. This function is exported by the :mod:`myhdl` package and
supplements the standard Python :func:`hex` and :func:`oct` conversion functions.

As a demonstration, we set up a simulation for a small width::

   sim = Simulation(testBench(width=3))
   sim.run()

The simulation produces the following output::

   % python bin2gray.py
   B: 000 | G: 000
   B: 001 | G: 001
   B: 010 | G: 011
   B: 011 | G: 010
   B: 100 | G: 110
   B: 101 | G: 111
   B: 110 | G: 101
   B: 111 | G: 100
   StopSimulation: No more events


.. _intro-slicing:

Bit slicing
-----------

.. index:: 
   single: bit slicing
   single: concat(); example usage

For a change, we will use a traditional function as an example to illustrate
slicing.  The following function calculates the HEC byte of an ATM header. ::

   from myhdl import intbv, concat

   COSET = 0x55

   def calculateHec(header):
       """ Return hec for an ATM header, represented as an intbv.

       The hec polynomial is 1 + x + x**2 + x**8.
       """
       hec = intbv(0)
       for bit in header[32:]:
           hec[8:] = concat(hec[7:2],
                            bit ^ hec[1] ^ hec[7],
                            bit ^ hec[0] ^ hec[7],
                            bit ^ hec[7]
                           )
       return hec ^ COSET

The code shows how slicing access and assignment is supported on the
:class:`intbv` data type. In accordance with the most common hardware
convention, and unlike standard Python, slicing ranges are downward. The code
also demonstrates concatenation of :class:`intbv` objects.

As in standard Python, the slicing range is half-open: the highest index bit is
not included. Unlike standard Python however, this index corresponds to the
*leftmost* item. Both indices can be omitted from the slice. If the leftmost
index is omitted, the meaning is to access "all" higher order bits.  If the
rightmost index is omitted, it is ``0`` by default.

The half-openness of a slice may seem awkward at first, but it helps to avoid
one-off count issues in practice. For example, the slice ``hex[8:]`` has exactly
``8`` bits. Likewise, the slice ``hex[7:2]`` has ``7-2=5`` bits. You can think
about it as follows: for a slice ``[i:j]``, only bits below index ``i`` are
included, and the bit with index ``j`` is the last bit included.

When an :class:`intbv` object is sliced, a new :class:`intbv` object is returned. 
This new :class:`intbv` object is always positive, and the value bounds are
set up in accordance with the bit width specified by the slice. For example::

    >>> a = intbv(6, min=-3, max=7)
    >>> len(a)
    4
    >>> b = a[4:]
    >>> b     
    intbv(6L)
    >>> len(b)
    4
    >>> b.min
    0
    >>> b.max
    16

In the example, the original object is sliced with a slice equal to its bit width.
The returned object has the same value and bit width, but its value
range consists of all positive values that can be represented by
the bit width.

The object returned by a slice is positive, even when the
original object is negative::

    >>> a = intbv(-3)
    >>> bin(a, width=5)
    '11101'
    >>> b = a[5:]
    >>> b
    intbv(29L)
    >>> bin(b)
    '11101'

The bit pattern of the two objects is identical within the bit width,
but their values have opposite sign.

.. _intro-signed:

Unsigned and signed representation
----------------------------------

.. index:: 
    single: intbv; intbv.signed

:class:`intbv` is designed to be as high level as possible. The underlying
value of an :class:`intbv` object is a Python :class:`int`, which is
represented as a two's complement number with "indefinite" bit
width. The range bounds are only used for error checking, and to
calculate the minimum required bit width for representation. As a
result, arithmetic can be performed like with normal integers.

In contrast, HDLs such as Verilog and VHDL typically require designers
to deal with representational issues, especially for synthesizable code.
They provide low-level types like ``signed`` and ``unsigned`` for
arithmetic. The rules for arithmetic with such types are much more
complicated than with plain integers.

In some cases it can be useful to interpret :class:`intbv` objects
in terms of "signed" and "unsigned". Basically, it depends on attribute *min*.
if *min* < 0, then the object is "signed", otherwise it is "unsigned".
In particular, the bit width of a "signed" object will account for
a sign bit, but that of an "unsigned" will not, because that would
be redundant. From earlier sections, we have learned that the
return value from a slicing operation is always "unsigned".

In some applications, it is desirable to convert an "unsigned"
:class:`intbv` to  a "signed", in other words, to interpret the msb bit
as a sign bit.  The msb bit is the highest order bit within the object's
bit width.  For this purpose, :class:`intbv` provides the
:meth:`intbv.signed` method. For example::

    >>> a = intbv(12, min=0, max=16)
    >>> bin(a)
    '1100'
    >>> b = a.signed()
    >>> b
    -4
    >>> bin(b, width=4)
    '1100'

:meth:`intbv.signed` extends the msb bit into the higher-order bits of the 
underlying object value, and returns the result as an integer.
Naturally, for a "signed" the return value will always be identical
to the original value, as it has the sign bit already.

As an example let's take a 8 bit wide data bus that would be modeled as
follows::

  data_bus = intbv(0)[8:]

Now consider that a complex number is transferred over this data
bus. The upper 4 bits of the data bus are used for the real value and
the lower 4 bits for the imaginary value. As real and imaginary values
have a positive and negative value range, we can slice them off from
the data bus and convert them as follows::

 real.next = data_bus[8:4].signed()
 imag.next = data_bus[4:].signed()


.. _intro-python:

Some concluding remarks on MyHDL and Python
===========================================

To conclude this introductory chapter, it is useful to stress that MyHDL is not
a language in itself. The underlying language is Python,  and MyHDL is
implemented as a Python package called ``myhdl``. Moreover, it is a design goal
to keep the ``myhdl`` package as minimalistic as possible, so that MyHDL
descriptions are very much "pure Python".

To have Python as the underlying language is significant in several ways:

* Python is a very powerful high level language. This translates into high
  productivity and elegant solutions to complex problems.

* Python is continuously improved by some very clever  minds, supported by a
  large and fast growing user base. Python profits fully from the open source
  development model.

* Python comes with an extensive standard library. Some functionality is likely
  to be of direct interest to MyHDL users: examples include string handling,
  regular expressions, random number generation, unit test support, operating
  system interfacing and GUI development. In addition, there are modules for
  mathematics, database connections, networking programming, internet data
  handling, and so on.

* Python has a powerful C extension model. All built-in types are written with
  the same C API that is available for custom extensions. To a module user, there
  is no difference between a standard Python module and a C extension module ---
  except performance. The typical Python development model is to prototype
  everything in Python until the application is stable, and (only) then rewrite
  performance critical modules in C if necessary.


.. _intro-summary:

Summary and perspective
=======================

Here is an overview of what we have learned in this chapter:

* Generators are the basic building blocks of MyHDL models. They provide the way
  to model massive concurrency and sensitivity lists.

* MyHDL provides decorators that create useful generators from local functions.

* Hardware structure and hierarchy is described with classic Python functions.

* :class:`Signal` objects are used to communicate between concurrent generators.

* :class:`intbv` objects are used to describe bit-oriented operations.

* A :class:`Simulation` object is used to simulate MyHDL models.

These concepts are sufficient to start describing and simulating MyHDL models.

However, there is much more to MyHDL. Here is an overview of what can be learned
from the following chapters:

* MyHDL supports sophisticated and high level modeling techniques. This is
  described in Chapter :ref:`model`.

* MyHDL enables the use of modern software verification techniques, such as unit
  testing, on hardware designs. This is the topic of Chapter :ref:`unittest`.

* It is possible to co-simulate MyHDL models with other HDL languages such as
  Verilog and VHDL. This is described in Chapter :ref:`cosim`.

* Last but not least, MyHDL models can be converted to Verilog, providing a path
  to a silicon implementation. This is the topic of Chapter :ref:`conv`.

.. rubric:: Footnotes

.. [#] The exception is the ``from module import *`` syntax, that imports all the
   symbols from a module. Although this is generally considered bad practice, it
   can be tolerated for large modules that export a lot of symbols. One may argue
   that ``myhdl`` falls into that category.

.. [#] All positional parameters have to go before any named parameter.

