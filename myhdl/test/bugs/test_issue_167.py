''' Bitonic sort '''

# http://www.myhdl.org/examples/bitonic/

import unittest
from random import randrange

from myhdl import Signal, intbv, \
  always_comb, instance, \
  delay, block, StopSimulation


ASCENDING = True
DESCENDING = False


# modules

@block
def compare(a_1, a_2, z_1, z_2, direction):
  """ Combinatorial circuit with two input and two output signals.
      Sorting to 'direction'. """

  @always_comb
  def logic():
    ''' Combinatorial logic '''
    if direction == (a_1 > a_2):
      z_1.next = a_2
      z_2.next = a_1
    else:
      z_1.next = a_1
      z_2.next = a_2

  return logic


@block
def feedthru(in_a, out_z):
  """ Equivalent of 'doing nothing'. """

  @always_comb
  def logic():
    ''' Combinatorial logic '''
    out_z.next = in_a

  return logic


@block
def bitonic_merge(list_a, list_z, direction):
  """ bitonicMerge:
      Generates the output from the input list of signals.
      Recursive. """
  len_list = len(list_a)
  half_len = len_list//2
  width    = len(list_a[0])

  if len_list > 1:
    tmp = [Signal(intbv(0)[width:]) for _ in range(len_list)]

    comp = [compare(list_a[i], list_a[i+half_len], tmp[i], tmp[i+half_len], \
                    direction) for i in range(half_len)]

    lo_merge = bitonic_merge( tmp[:half_len], list_z[:half_len], direction )
    hi_merge = bitonic_merge( tmp[half_len:], list_z[half_len:], direction )

    return comp, lo_merge, hi_merge
  else:
    feed = feedthru(list_a[0], list_z[0])
    return feed


@block
def bitonic_sort(list_a, list_z, direction):
  """ bitonicSort:
      Produces a bitonic sequence.
      Recursive. """
  len_list = len(list_a)
  half_len = len_list//2
  width    = len(list_a[0])

  if len_list > 1:
    tmp = [Signal(intbv(0)[width:]) for _ in range(len_list)]

    lo_sort = bitonic_sort( list_a[:half_len], tmp[:half_len], ASCENDING  )
    hi_sort = bitonic_sort( list_a[half_len:], tmp[half_len:], DESCENDING )

    merge = bitonic_merge( tmp, list_z, direction )
    return lo_sort, hi_sort, merge
  else:
    feed = feedthru(list_a[0], list_z[0])
    return feed


# tests

@block
def array8sorter(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7,
                 z_0, z_1, z_2, z_3, z_4, z_5, z_6, z_7):
  ''' Sort Array with 8 values '''

  list_a = [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]
  list_z = [z_0, z_1, z_2, z_3, z_4, z_5, z_6, z_7]

  sort = bitonic_sort(list_a, list_z, ASCENDING)
  return sort


class TestBitonicSort(unittest.TestCase):
  ''' Test class for bitonic sort '''

  def test_sort(self):
    """ Check the functionality of the bitonic sort """
    length = 8
    width  = 4

    @block
    def test_impl():
      ''' test implementation '''
      inputs  = [ Signal(intbv(0)[width:]) for _ in range(length) ]
      outputs = [ Signal(intbv(0)[width:]) for _ in range(length) ]
      z_0, z_1, z_2, z_3, z_4, z_5, z_6, z_7 = outputs
      a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7 = inputs

      inst = array8sorter(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7,
                          z_0, z_1, z_2, z_3, z_4, z_5, z_6, z_7)

      @instance
      def check():
        ''' testbench input and validation '''
        for i in range(100):
          data = [randrange(2**width) for i in range(length)]
          for i in range(length):
            inputs[i].next = data[i]
          yield delay(10)
          data.sort()
          self.assertEqual(data, outputs, 'wrong data')
        raise StopSimulation

      return inst, check

    inst = test_impl()
    inst.run_sim()


# convert

def test_issue_167():
  ''' Convert to VHDL '''
  length = 8
  width  = 4
  sigs = [Signal(intbv(0)[width:]) for _ in range(2*length)]

  inst = array8sorter( *sigs )
  inst.convert( hdl='VHDL' )

if __name__ == '__main__':
  test_issue_167()
