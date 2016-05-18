.. currentmodule:: myhdl

.. testsetup:: *

   from myhdl import *

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

:class:`intbv` supports the same operators as :class:`int` for arithmetic. In
addition, it provides a number of features to make it suitable for hardware
design. First, the range of allowed values can be constrained. This makes it
possible to check the value at run time during simulation. Moreover, back end
tools can determine the smallest possible bit width for representing the object.
Secondly, it supports bit level operations by providing an indexing and slicing
interface.

:class:`intbv` objects are constructed in general as follows::

    intbv([val=None] [, min=None]  [, max=None])

*val* is the initial value. *min* and *max* can be used to constrain
the value. Following the Python conventions, *min* is inclusive, and
*max* is exclusive. Therefore, the allowed value range is *min* .. *max*-1.

Let's look at some examples. An unconstrained :class:`intbv` object is created
as follows::

  >>> a = intbv(24)

.. index::
    single: intbv; min
    single: intbv; max
    single: intbv; bit width

After object creation, *min* and *max* are available as attributes for
inspection. Also, the standard Python function :func:`len` can be used
to determine the bit width. If we inspect the previously created
object, we get::

  >>> a
  intbv(24)
  >>> print(a.min)
  None
  >>> print(a.max)
  None
  >>> len(a)
  0

As the instantiation was unconstrained, the *min* and *max* attributes
are undefined. Likewise, the bit width is undefined, which is indicated
by a return value ``0``.

A constrained :class:`intbv` object is created as follows:

  >>> a = intbv(24, min=0, max=25)

Inspecting the object now gives::

  >>> a
  intbv(24)
  >>> a.min
  0
  >>> a.max
  25
  >>> len(a)
  5

We see that the allowed value range is 0 .. 24,  and that 5 bits are
required to represent the object.

The *min* and *max* bound attributes enable fine-grained control and error
checking of the value range. In particular, the bound values do not have to be
symmetric or powers of 2. In all cases, the bit width is set appropriately to
represent the values in the range. For example::

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

A common requirement in hardware design is access to the individual bits. The
:class:`intbv` class implements an indexing interface that provides access to
the bits of the underlying two's complement representation. The following
illustrates bit index read access::

  >>> from myhdl import bin
  >>> a = intbv(24)
  >>> bin(a)
  '11000'
  >>> int(a[0])
  0
  >>> int(a[3])
  1
  >>> b = intbv(-23)
  >>> bin(b)
  '101001'
  >>> int(b[0])
  1
  >>> int(b[3])
  1
  >>> int(b[4])
  0

We use the :func:`bin` function provide by MyHDL because it shows the two's
complement representation for negative values, unlike Python's builtin with the
same name. Note that lower indices correspond to less significant bits. The
following code illustrates bit index assignment::

  >>> bin(a)
  '11000'
  >>> a[3] = 0
  >>> bin(a)
  '10000'
  >>> a
  intbv(16)
  >>> b
  intbv(-23)
  >>> bin(b)
  '101001'
  >>> b[3] = 0
  >>> bin(b)
  '100001'
  >>> b
  intbv(-31)

.. _hwtypes-slicing:

Bit slicing
===========

.. index::
   single: bit slicing

The :class:`intbv` type also supports bit slicing, for both read access
assignment. For example::

   >>> a = intbv(24)
   >>> bin(a)
   '11000'
   >>> a[4:1]
   intbv(4)
   >>> bin(a[4:1])
   '100'
   >>> a[4:1] = 0b001
   >>> bin(a)
   '10010'
   >>> a
   intbv(18)

In accordance with the most common hardware convention, and unlike standard
Python, slicing ranges are downward.  As in standard Python, the slicing range
is half-open: the highest index bit is not included. Unlike standard Python
however, this index corresponds to the *leftmost* item.

Both indices can be omitted from the slice.  If the rightmost index is omitted,
it is ``0`` by default. If the leftmost index is omitted, the meaning is to
access "all" higher order bits. For example::

  >>> bin(a)
  '11000'
  >>> bin(a[4:])
  '1000'
  >>> a[4:] = '0001'
  >>> bin(a)
  '10001'
  >>> a[:] = 0b10101
  >>> bin(a)
  '10101'

The half-openness of a slice may seem awkward at first, but it helps to avoid
one-off count issues in practice. For example, the slice ``a[8:]`` has exactly
``8`` bits. Likewise, the slice ``a[7:2]`` has ``7-2=5`` bits. You can think
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

The object returned by a slice is positive, even when the original object is
negative::

    >>> a = intbv(-3)
    >>> bin(a, width=5)
    '11101'
    >>> b = a[5:]
    >>> b
    intbv(29L)
    >>> bin(b)
    '11101'

In this example, the bit pattern of the two objects is identical within the bit
width, but their values have opposite sign.

Sometimes hardware engineers prefer to constrain an object by defining its bit
width directly, instead of the range of allowed values. Using the slicing
properties of the :class:`intbv` class one can do that as follows::

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
the range 0 .. 31.  Creating an :class:`intbv` in this way is convenient but has
the disadvantage that only positive value ranges between 0 and a power of 2 can
be specified.

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
:class:`modbv`. For example, the modulo counter above can be
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
