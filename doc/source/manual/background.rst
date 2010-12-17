.. currentmodule:: myhdl

.. _background:

**********************
Background information
**********************


.. _prerequisites:

Prerequisites
=============

You need a basic understanding of Python to use MyHDL. If you don't know Python,
don't worry: it is is one of the easiest programming languages to learn  [#]_.
Learning Python is one of the best time investments that engineering
professionals can make  [#]_.

For starters, http://docs.python.org/tutorial is probably the
best choice for an on-line tutorial. For alternatives, see
http://wiki.python.org/moin/BeginnersGuide.

A working knowledge of a hardware description language such as Verilog or VHDL
is helpful.

Code examples in this manual are sometimes shortened for clarity. Complete
executable examples can be found in the distribution directory at
:file:`example/manual/`.


.. _tutorial:

A small tutorial on generators
==============================

.. index:: single: generators; tutorial on

Generators were introduced in
Python 2.2. Because generators are the key concept in MyHDL, a small tutorial is
included here.

Consider the following nonsensical function::

   def function():
       for i in range(5):
           return i

You can see why it doesn't make a lot of sense. As soon as the first loop
iteration is entered, the function returns::

   >>> function()
   0

Returning is fatal for the function call. Further loop iterations never get a
chance, and nothing is left over from the function call when it returns.

To change the function into a generator function, we replace :keyword:`return`
with :keyword:`yield`::

   def generator():
       for i in range(5):
           yield i

Now we get::

   >>> generator()
   <generator object at 0x815d5a8>

When a generator function is called, it returns a generator object. A generator
object supports the iterator protocol, which is an expensive way of saying that
you can let it generate subsequent values by calling its :func:`next` method::

   >>> g = generator()
   >>> g.next()
   0
   >>> g.next()
   1
   >>> g.next()
   2
   >>> g.next()
   3
   >>> g.next()
   4
   >>> g.next()
   Traceback (most recent call last):
     File "<stdin>", line 1, in ?
   StopIteration

Now we can generate the subsequent values from the for loop on demand, until
they are exhausted. What happens is that the :keyword:`yield` statement is like
a :keyword:`return`, except that it is non-fatal: the generator remembers its
state and the point in the code when it yielded. A higher order agent can decide
when to get the next value by calling the generator's :func:`next` method. We
say that generators are :dfn:`resumable functions`.

.. index::
   single: VHDL; process
   single: Verilog; always block

If you are familiar with hardware description languages, this may ring a bell.
In hardware simulations, there is also a higher order agent, the Simulator, that
interacts with such resumable functions; they are called  :dfn:`processes` in
VHDL and  :dfn:`always blocks` in Verilog.  Similarly, Python generators provide
an elegant and efficient method to model concurrency, without having to resort
to some form of threading.

.. index:: single: sensitivity list

The use of generators to model concurrency is the first key concept in MyHDL.
The second key concept is a related one: in MyHDL, the yielded values are used
to specify the conditions on which the generator should wait before resuming. In
other words, :keyword:`yield` statements work as general  sensitivity lists.

.. _deco:

About decorators
================

.. index:: single: decorators; about

Python 2.4 introduced a feature called decorators. MyHDL takes advantage
of this feature by defining a number of decorators that facilitate hardware
descriptions. However, some users may not yet be familiar with decorators.
Therefore, an introduction is included here.

A decorator consists of special syntax in front of a function declaration. It
refers to a decorator function. The decorator function automatically transforms
the declared function into some other callable object.

A decorator function :func:`deco` is used in a decorator statement as follows::

   @deco
   def func(arg1, arg2, ...):
       <body>

This code is equivalent to the following::

   def func(arg1, arg2, ...):
       <body>
   func = deco(func)

Note that the decorator statement goes directly in front of the function
declaration, and that the function name :func:`func` is automatically reused for
the final result.

MyHDL uses decorators to create ready-to-simulate generators from local
function definitions. Their functionality and usage will be described
extensively in this manual.

.. rubric:: Footnotes

.. [#] You must be bored by such claims, but in Python's case it's true.

.. [#] I am not biased.

