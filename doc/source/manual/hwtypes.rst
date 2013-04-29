.. currentmodule:: myhdl

.. _hwtypes:

***********************
Hardware-oriented types
***********************

.. _hwtypes-intbv:

The :class:`intbv` class
========================

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


Note that the *max* attribute is 32, as with 5 bits it is possible to represent
the range 0 .. 31.  Creating an :class:`intbv` this way has the disadvantage
that only positive value ranges can be specified. Slicing is described in more
detail in :ref:`hwtypes-slicing`.

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


.. _hwtypes-indexing:

Bit indexing
============

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


.. _hwtypes-slicing:

Bit slicing
===========

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

.. _hwtypes-modbv:

The :class:`modbv` class
========================

In hardware modeling, there is often a need for the elegant modeling of
wrap-around behavior. :class:`intbv` instances do not support this
automatically, as they assert that any assigned value is within the bound
constraints. However, wrap-around modeling can be straightforward.  For
example, the wrap-around condition for a counter is often decoded explicitly,
as it is needed for other purposes. Also, the modulo operator provides an
elegant one-liner in many scenarios::

    count.next = (count + 1) % 2**8

However, some interesting cases are not supported by the :class:`intbv` type.
For example, we would like to describe a free running counter using a variable
and augmented assignment as follows::

    count_var += 1

This is not possible with the :class:`intbv` type, as we cannot add the modulo
behavior to this description. A similar problem exist for an augmented left
shift as follows::

    shifter <<= 4

To support these operations directly, MyHDL provides the :class:`modbv`
type. :class:`modbv` is implemented as a subclass of  :class:`intbv`.
The two classes have an identical interface and work together
in a straightforward way for arithmetic operations.
The only difference is how the bounds are handled: out-of-bound values
result in an error with :class:`intbv`, and in wrap-around with
:class:`modbv`. For example, the modulo counter as above can be
modeled as follows::

    count = Signal(modbv(0, min=0, max=2**8))
    ...
    count.next = count + 1

The wrap-around behavior is defined in general as follows::

    val = (val - min) % (max - min) + min

In a typical case when ``min==0``, this reduces to::

    val = val % max

.. _hwtypes-signed:

Unsigned and signed representation
==================================

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


