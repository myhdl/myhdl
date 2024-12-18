'''
Created on 3 dec. 2024

@author: josy
'''

import sys
import inspect
import collections

from abc import ABC, abstractmethod

from myhdl import block
from myhdl._misc import _isGenSeq
from myhdl._block import _Block

ForwardPort = collections.namedtuple('ForwardPort', ['hdlblock', 'port'])


class HdlClass(ABC):
    '''
        This Abstract Base Class 
    '''

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    @block(skipname=True)
    def hdl(self):
        ''' 
            placeholder for user written hdl 
            
            do not forget the `@block(skipname=True)` to skip adding '_hdl' in the name chain ...
        '''
        pass

    @block(skipname=True)
    def hdlinstances(self):
        ''' return the hdl() of the instantiated building blocks '''
        # it needs a 'block decorator', because we we will call on the subsequent .hdl() methods ...
        # luckily we can now skip the adding of '_hdlinstances' in the name chain ...
        # THIS doesn't look that great - the Simulator wiil show an intermediate block (this one)
        # as 'None', and that really doesn't look nice
        # BUT we have handled (hacked?) it in _tracesignals.py

        frame = inspect.currentframe()
        loi = []
        try:
            outerframes = inspect.getouterframes(frame)
            dlocals = outerframes[3][0].f_locals
            keys = dlocals.keys()
            values = dlocals.values()

            # now collect the hdl() and other logic generators
            for key, value in zip(keys, values):
                if isinstance(value, list):
                    if len(value):
                        if isinstance(value[0], HdlClass):
                            idx = 0
                            for item in value:
                                if id(item) != id(self):
                                    thdl = item.hdl()
                                    thdl.name = f'{key}{idx}'
                                    idx += 1
                                    loi.append(thdl)
                        elif _isGenSeq(value):
                            loi.append(value)

                elif isinstance(value, HdlClass):
                    if id(value) != id(self):
                        thdl = value.hdl()
                        thdl.name = f'{key}'
                        loi.append(thdl)

                # note that the always_xxx generators are also in keys/values
                elif _isGenSeq(value):
                    # just use the instance
                    loi.append(value)

                else:
                    pass

        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

        del frame

        return loi

