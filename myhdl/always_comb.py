from __future__ import generators

import inspect
from types import FunctionType

from util import _isgeneratorfunction
from pprint import pprint

class Error(Exception):
    """Cosimulation Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class ArgumentError(Error):
    """ always_comb argument should be a normal (non-generator) function"""
    
class NrOfArgsError(Error):
    """ always_comb argument should be a function without arguments"""

class ScopeError(Error):
    """always_comb should be called with a local function as argument"""

def always_comb(func):
    f = inspect.getouterframes(inspect.currentframe())[1][0]
    if type(func) is not FunctionType:
        raise ArgumentError
    if _isgeneratorfunction(func):
        raise ArgumentError
    if func.func_code.co_argcount:
        raise NrOfArgsError
    if func.func_name not in f.f_locals:
        raise ScopeError
