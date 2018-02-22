from __future__ import absolute_import
import myhdl
from myhdl import *


def glibc_random(seed):
    random_word = intbv(0)[64:]
    random_word[:] = seed * 1103515245 + 12345
    return random_word[32:]
