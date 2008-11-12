
.. module:: myhdl

.. _ref:

*********
Reference
*********


MyHDL is implemented as a Python package called :mod:`myhdl`. This chapter
describes the objects that are exported by this package.


.. _ref-sim:

Simulation
==========


.. _ref-simclass:

The :class:`Simulation` class
-----------------------------




.. class:: Simulation(arg [, arg ...])

   Class to construct a new simulation. Each argument should be a MyHDL instance.
   In MyHDL, an instance is recursively defined as being either a sequence of
   instances, or a MyHDL generator, or a Cosimulation object. See section
   :ref:`ref-gen` for the definition of MyHDL generators and their interaction with
   a :class:`Simulation` object.  See Section :ref:`ref-cosim` for the
   :class:`Cosimulation` object.  At most one :class:`Cosimulation` object can be
   passed to a :class:`Simulation` constructor.

A :class:`Simulation` object has the following method:


.. method:: Simulation.run([duration])

   Run the simulation forever (by default) or for a specified duration.


.. _ref-simsupport:

Simulation support functions
----------------------------




.. function:: now()

   Returns the current simulation time.


.. exception:: StopSimulation()

   Base exception that is caught by the ``Simulation.run()`` method to stop a
   simulation.


.. _ref-trace:

Waveform tracing
----------------


.. function:: traceSignals(func [, *args] [, **kwargs])

   Enables signal tracing to a VCD file for waveform viewing. *func* is a function
   that returns an instance. :func:`traceSignals` calls *func* under its control
   and passes *\*args* and *\*\*kwargs* to the call. In this way, it finds the
   hierarchy and the signals to be traced.

   The return value is the same as would be returned by the call ``func(*args,
   **kwargs)``.  The top-level instance name and the basename of the VCD output
   filename is ``func.func_name`` by default. If the VCD file exists already, it
   will be moved to a backup file by attaching a timestamp to it, before creating
   the new file.

The ``traceSignals`` callable has the following attribute:


.. attribute:: traceSignals.name

   This attribute is used to overwrite the default top-level instance name and the
   basename of the VCD output filename.


.. _ref-model:

Modeling
========


.. _ref-sig:

The :class:`Signal` class
-------------------------




.. class:: Signal([val=None] [, delay=0])

   This class is used to construct a new signal and to initialize its value to
   *val*. Optionally, a delay can be specified.

A :class:`Signal` object has the following attributes:


.. attribute:: Signal.posedge

   Attribute that represents the positive edge of a signal, to be used in
   sensitivity lists.


.. attribute:: Signal.negedge

   Attribute that represents the negative edge of a signal, to be used in
   sensitivity lists.


.. attribute:: Signal.next

   Read-write attribute that represents the next value of the signal.


.. attribute:: Signal.val

   Read-only attribute that represents the current value of the signal.

   This attribute is always available to access the current value; however in many
   practical case it will not be needed. Whenever there is no ambiguity, the Signal
   object's current value is used implicitly. In particular, all Python's standard
   numeric, bit-wise, logical and comparison operators are implemented on a Signal
   object by delegating to its current value. The exception is augmented
   assignment. These operators are not implemented as they would break the rule
   that the current value should be a read-only attribute. In addition, when a
   Signal object is assigned to the ``next`` attribute of another Signal object,
   its current value is assigned instead.


.. attribute:: Signal.min

   Read-only attribute that is the minimum value (inclusive) of a numeric signal,
   or *None* for no minimum.


.. attribute:: Signal.max

   Read-only attribute that is the maximum value (exclusive) of a numeric signal,
   or *None* for no  maximum.


.. attribute:: Signal.driven

   Writable attribute that can be used to indicate that the signal is supposed to
   be driven from the MyHDL code, and how it should be declared in Verilog after
   conversion. The allowed values are ``'reg'`` and ``'wire'``.

   This attribute is useful when the Verilog converter cannot infer automatically
   whether and how a signal is driven. This occurs when the signal is driven from
   user-defined Verilog code.


.. _ref-gen:

MyHDL generators and trigger objects
------------------------------------



.. index:: single: sensitivity list

MyHDL generators are standard Python generators with specialized
:keyword:`yield` statements. In hardware description languages, the equivalent
statements are called  *sensitivity lists*. The general format of
:keyword:`yield` statements in in MyHDL generators is:

.. % 

When a generator executes a :keyword:`yield` statement, its execution is
suspended at that point. At the same time, each *clause* is a *trigger object*
which defines the condition upon which the generator should be resumed. However,
per invocation of a :keyword:`yield` statement, the generator resumes exactly
once, regardless of the number of clauses. This happens on the first trigger
that occurs.

In this section, the trigger objects and their functionality will be described.

Some MyHDL objects that are described elsewhere can directly be used as trigger
objects. In particular, a signal can be used as a trigger object. Whenever a
signal changes value, the generator resumes. Likewise, the objects referred to
by the signal attributes ``posedge`` and ``negedge`` are trigger objects. The
generator resumes on the occurrence of a positive or a negative edge on the
signal, respectively. An edge occurs when there is a change from false to true
(positive) or vice versa (negative). For the full description of the
:class:`Signal` class and its attributes, see section :ref:`ref-sig`.

Furthermore, MyHDL generators can be used as clauses in ``yield`` statements.
Such a generator is forked, and starts operating immediately, while the original
generator waits for it to complete. The original generator resumes when the
forked generator returns.

In addition, the following functions return trigger objects:


.. function:: delay(t)

   Return a trigger object that specifies that the generator should resume after a
   delay *t*.


.. function:: join(arg [, arg ...])

   Join a number of trigger objects together and return a joined trigger object.
   The effect is that the joined trigger object will trigger when *all* of its
   arguments have triggered.

Finally, as a special case, the Python ``None`` object can be present in a
``yield`` statement. It is the do-nothing trigger object. The generator
immediately resumes, as if no ``yield`` statement were present. This can be
useful if the ``yield`` statement also has generator clauses: those generators
are forked, while the original generator resumes immediately.


.. _ref-deco:

Decorator functions
-------------------

.

MyHDL defines a number of decorator functions, that make it easier to create
generators from local generator functions.


.. function:: instance()

   The :func:`instance` decorator is the most general decorator.  It automatically
   creates a generator by calling the decorated generator function.

   It is used as follows::

      def top(...):
          ...
          @instance
          def inst():
              <generator body>
          ...
          return inst, ...

   This is equivalent to::

      def top(...):
          ...
          def _gen_func():
              <generator body>
          ...
          inst = _gen_func()
          ...
          return inst, ...


.. function:: always(arg [, *args])

   The :func:`always` decorator is a specialized decorator that targets a widely
   used coding pattern. It is used as follows::

      def top(...):
          ...
          @always(event1, event2, ...)
          def inst()
              <body>
          ...
          return inst, ...

   This is equivalent to the following::

      def top(...):
          ...
          def _func():
              <body>

          def _gen_func()
              while True:
                  yield event1, event2, ... 
                  _func()
          ...
          inst = _gen_func()
          ...
          return inst, ...

   The argument list of the decorator corresponds to the sensitivity list. Only
   signals, edge specifiers, or delay objects are allowed. The decorated function
   should be a classic function.


.. function:: always_comb()

   The :func:`always_comb` decorator is used to describe combinatorial logic. ::

      def top(...):
          ...
          @always_comb
          def comb_inst():
              <combinatorial body>
          ...
          return comb_inst, ...

   The :func:`always_comb` decorator infers the inputs of the combinatorial logic
   and the corresponding sensitivity list automatically. The decorated function
   should be a classic function.


.. _ref-intbv:

The :class:`intbv` class
------------------------




.. class:: intbv([val=None] [, min=None]  [, max=None])

   This class represents :class:`int`\ -like objects with some additional features
   that make it suitable for hardware design. The *val* argument can be an
   :class:`int`, a :class:`long`, an :class:`intbv` or a bit string (a string with
   only '0's or '1's). For a bit string argument, the value is calculated as in
   ``int(bitstring, 2)``.  The optional *min* and *max* arguments can be used to
   specify the minimum and maximum value of the :class:`intbv` object. As in
   standard Python practice for ranges, the minimum value is inclusive and the
   maximum value is exclusive.

The minimum and maximum values of an :class:`intbv` object are available as
attributes:


.. attribute:: intbv.min

   Read-only attribute that is the minimum value (inclusive) of an :class:`intbv`,
   or *None* for no minimum.


.. attribute:: intbv.max

   Read-only attribute that is the maximum value (exclusive) of an :class:`intbv`,
   or *None* for no  maximum.

.. method:: intbv.signed()

   Return the bits as specified by the *_nrbits* attribute of the :class:`intbv` 
   value as two's complement number when classified as 'unsigned'. The value is 
   classfied as 'unsigned' if the *min* attribute is >= 0 and *max* > *min*. 
   Bit # *_nrbits*-1 specifies then the sign of the value.

   :rtype: integer

Unlike :class:`int` objects, :class:`intbv` objects are mutable; this is also
the reason for their existence. Mutability is needed to support assignment to
indexes and slices, as is common in hardware design. For the same reason,
:class:`intbv` is not a subclass from :class:`int`, even though :class:`int`
provides most of the desired functionality. (It is not possible to derive a
mutable subtype from an immutable base type.)

An :class:`intbv` object supports the same comparison, numeric, bitwise,
logical, and conversion operations as :class:`int` objects. See
http://www.python.org/doc/current/lib/typesnumeric.html for more information on
such operations. In all binary operations, :class:`intbv` objects can work
together with :class:`int` objects. For mixed-type numeric operations, the
result type is an :class:`int` or a :class:`long`. For mixed-type bitwise
operations, the result type is an :class:`intbv`.

In addition, :class:`intbv` objects support indexing and slicing operations:

+-----------------+---------------------------------+--------+
| Operation       | Result                          | Notes  |
+=================+=================================+========+
| ``bv[i]``       | item *i* of *bv*                | \(1)   |
+-----------------+---------------------------------+--------+
| ``bv[i] = x``   | item *i* of *bv* is replaced by | \(1)   |
|                 | *x*                             |        |
+-----------------+---------------------------------+--------+
| ``bv[i:j]``     | slice of *bv* from *i* downto   | (2)(3) |
|                 | *j*                             |        |
+-----------------+---------------------------------+--------+
| ``bv[i:j] = t`` | slice of *bv* from *i* downto   | (2)(4) |
|                 | *j* is replaced by *t*          |        |
+-----------------+---------------------------------+--------+

(1)
   Indexing follows the most common hardware design conventions: the lsb bit is the
   rightmost bit, and it has index 0. This has the following desirable property: if
   the :class:`intbv` value is decomposed as a sum of powers of 2, the bit with
   index *i* corresponds to the term ``2**i``.

(2)
   In contrast to standard Python sequencing conventions, slicing range are
   downward. This is a consequence of the indexing convention, combined with the
   common convention that the most significant digits of a number are the leftmost
   ones. The Python convention of half-open ranges is followed: the bit with the
   highest index is not included. However, it is the *leftmost* bit in this case.
   As in standard Python, this takes care of one-off issues in many practical
   cases: in particular, ``bv[i:]`` returns *i* bits; ``bv[i:j]`` has ``i-j`` bits.
   When the low index *j* is omitted, it defaults to ``0``. When the high index *i*
   is omitted, it means "all" higher order bits.

(3)
   The object returned from a slicing access operation is always a positive
   :class:`intbv`; higher order bits are implicitly assumed to be zero. The bit
   width is implicitly stored in the return object, so that it can be used in
   concatenations and as an iterator. In addition, for a bit width w, the *min* and
   *max* attributes are implicitly set to ``0`` and ``2**w``, respectively.

(4)
   When setting a slice to a value, it is checked whether the slice is wide enough.

In addition, an :class:`intbv` object supports the iterator protocol. This makes
it possible to iterate over all its bits, from the high index to index 0. This
is only possible for :class:`intbv` objects with a defined bit width.


.. _ref-model-misc:

Miscellaneous modeling support functions
----------------------------------------




.. function:: bin(num [, width])

   Returns a bit string representation. If the optional *width* is provided, and if
   it is larger than the width of the default representation, the bit string is
   padded with the sign bit.

   This function complements the standard Python conversion functions ``hex`` and
   ``oct``. A binary string representation is often useful in hardware design.

   :rtype: string


.. function:: concat(base [, arg ...])

   Returns an :class:`intbv` object formed by concatenating the arguments.

   The following argument types are supported: :class:`intbv` objects with a
   defined bit width, :class:`bool` objects, signals of the previous objects, and
   bit strings. All these objects have a defined bit width. The first argument
   *base* is special as it doesn't need to have a defined bit width. In addition to
   the previously mentioned objects, unsized :class:`intbv`, :class:`int` and
   :class:`long` objects are supported, as well as signals of such objects.

   :rtype: :class:`intbv`

.. function:: downrange(high [, low=0])

   Generates a downward range list of integers.

   This function is modeled after the standard ``range`` function, but works in the
   downward direction. The returned interval is half-open, with the *high* index
   not included. *low* is optional and defaults to zero.  This function is
   especially useful in conjunction with the :class:`intbv` class, that also works
   with downward indexing.


.. function:: enum(arg [, arg ...] [, encoding='binary'])

   Returns an enumeration type.

   The arguments should be string literals that represent the desired names of the
   enumeration type attributes.  The returned type should be assigned to a type
   name.  For example::

      t_EnumType = enum('ATTR_NAME_1', 'ATTR_NAME_2', ...)

   The enumeration type identifiers are available as attributes of the type name,
   for example: ``t_EnumType.ATTR_NAME_1``

   The optional keyword argument *encoding* specifies the encoding scheme used in
   Verilog output. The available encodings are ``'binary'``, ``'one_hot'``, and
   ``'one_cold'``.


.. function:: instances()

   Looks up all MyHDL instances in the local name space and returns them in a list.

   :rtype: list


.. _ref-cosim:

Co-simulation
=============




.. _ref-cosim-myhdl:

MyHDL
-----


.. class:: Cosimulation(exe, **kwargs)

   Class to construct a new Cosimulation object.

   The *exe* argument is a command string to execute an HDL simulation. The
   *kwargs* keyword arguments provide a named association between signals (regs &
   nets) in the HDL simulator and signals in the MyHDL simulator. Each keyword
   should be a name listed in a ``$to_myhdl`` or ``$from_myhdl`` call in the HDL
   code. Each argument should be a :class:`Signal` declared in the MyHDL code.


.. _ref-cosim-verilog:

Verilog
-------


.. function:: $to_myhdl(arg, [, arg ...])

   Task that defines which signals (regs & nets) should be read by the MyHDL
   simulator. This task should be called at the start of the simulation.


.. function:: $from_myhdl(arg, [, arg ...])

   Task that defines which signals should be driven by the MyHDL simulator. In
   Verilog, only regs can be specified. This task should be called at the start of
   the simulation.



.. _ref-conv:

Conversion to Verilog and VHDL
==============================



.. _ref-conv-conv:

Conversion
----------


.. function:: toVerilog(func [, *args] [, **kwargs])

   Converts a MyHDL design instance to equivalent Verilog code, and also generates
   a test bench to verify it. *func* is a function that returns an instance.
   :func:`toVerilog` calls *func* under its control and passes *\*args* and
   *\*\*kwargs* to the call.

   The return value is the same as would be returned by the call ``func(*args,
   **kwargs)``. It should be assigned to an instance name.

   The top-level instance name and the basename of the Verilog output filename is
   ``func.func_name`` by default.

   For more information about the restrictions on convertible MyHDL code, see
   section :ref:`conv-subset` in Chapter :ref:`conv`.

:func:`toVerilog` has the following attribute:


.. attribute:: toVerilog.name

   This attribute is used to overwrite the default top-level instance name and the
   basename of the Verilog output filename.



.. function:: toVHDL(func[, *args][, **kwargs])

   Converts a MyHDL design instance to equivalent VHDL
   code. *func* is a function that returns an instance. :func:`toVHDL`
   calls *func* under its control and passes *\*args* and
   *\*\*kwargs* to the call.

   The return value is the same as would be returned by the call
   ``func(*args, **kwargs)``. It can be assigned to an instance name.
   The top-level instance name and the basename of the Verilog
   output filename is ``func.func_name`` by default.
	
:func:`toVHDL` has the following attributes:

.. attribute:: toVHDL.name

  This attribute is used to overwrite the default top-level
  instance name and the basename of the VHDL output.

.. attribute:: toVHDL.component_declarations

  This attribute can be used to add component declarations to the
  VHDL output. When a string is assigned to it, it will be copied
  to the appropriate place in the output file.



.. _ref-conv-user:

User-defined Verilog and VHDL code
----------------------------------

A user can insert user-defined code in the Verilog or VHDL output by using the
``__verilog__`` or ``__vhdl__`` hook respectively.


.. data:: __verilog__

   When defined within a function under elaboration, this
   variable specifies user-defined code that should be used instead of Verilog converted
   code for that function.  The user-defined code should be a Python format string
   that uses keys to refer to the variables that should be interpolated in the
   string. Any variable in the function context can be referred to.


.. data:: __vhdl__

   When defined within a function under elaboration, this
   variable specifies user-defined code that should be used instead of VHDL converted
   code for that function.  The user-defined code should be a Python format string
   that uses keys to refer to the variables that should be interpolated in the
   string. Any variable in the function context can be referred to.


These hooks cannot be used inside generator functions or decorated local
functions, as these are not elaborated. In other words, they should be used 
in functions that define structure.



Conversion output verification
==============================

.. module:: myhdl.conversion

Verification interface
----------------------

All functions related to conversion verification are implemented in
the :mod:`myhdl.conversion` package.

.. function:: verify(func[, *args][, **kwargs])

  Used like :func:`toVHDL()`. It converts MyHDL code,
  simulates both the MyHDL code and the HDL code and reports any
  differences. The default HDL simulator is GHDL.

.. function:: analyze(func[, *args][, **kwargs])

  Used like :func:`toVHDL()`. It converts MyHDL code, and analyzes the
  resulting HDL. 
  Used to verify whether the HDL output is syntactically correct.

The two previous functions have the following attribute:

.. attribute:: analyze.simulator

  Used to set the name of the HDL analyzer. GHDL
  is the default.

.. attribute:: verify.simulator

  Used to set the name of the HDL simulator. GHDL
  is the default.

HDL simulator registration
--------------------------

To be able to use a HDL simulator to verify conversions, it needs to
be registered first. This is needed once per simulator (or rather, per
set of analysis and simulation commands). Registering is done with the
following function:

.. function:: registerSimulator(name=None, hdl=None, analyze=None, elaborate=None, simulate=None, offset=0)

   Registers a particular HDL simulator to be used by  :func:`verify()`
   and :func:`analyze()`. *name* is the name of the simulator.
   *hdl* specifies the HDL: ``"VHDL"`` or ``"Verilog"``.
   *analyze* is a command string to analyze the HDL source code.
   *elaborate* is a command string to elaborate the HDL
   code. This command is optional.
   *simulate* is a command string to simulate the HDL code.
   *offset* is an integer specifying the number of initial lines to be ignored
   from the HDL simulator output. 

   The command strings should be string templates that refer to the
   ``topname`` variable that specifies the design name. The templates
   can also use the ``unitname`` variable which is the lower case
   version of ``topname``.
   The command strings can assume that a subdirectory called
   ``work`` is available in the current working directory. Analysis and
   elaboration results can be put there if desired.

   The :func:`analyze()` function uses the *analyze* command.
   The :func:`verify()` function uses the *analyze* command, then the
   *elaborate* command if any, and then the *simulate* command.


Preregistered HDL simulators
----------------------------

A number of open-source HDL simulators are preregistered in the
MyHDL distribution, as follows:

GHDL
^^^^

::

    registerSimulator(
        name="GHDL",
        hdl="VHDL",
        analyze="ghdl -a --workdir=work pck_myhdl_%(version)s.vhd %(topname)s.vhd",
        elaborate="ghdl -e --workdir=work -o %(unitname)s_ghdl %(topname)s",
        simulate="ghdl -r %(unitname)s_ghdl"
        )


Icarus 
^^^^^^

::

    registerSimulator(
        name="icarus",
        hdl="Verilog",
        analyze="iverilog -o %(topname)s.o %(topname)s.v",
        simulate="vvp %(topname)s.o"
        )


cver
^^^^

::

    registerSimulator(
        name="cver",
        hdl="Verilog",
        analyze="cver -c -q %(topname)s.v",
        simulate="cver -q %(topname)s.v",
        offset=3
        )
