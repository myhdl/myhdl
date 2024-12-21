'''
Created on 3 dec. 2024

@author: josy
'''

import sys
import inspect

from abc import ABC, abstractmethod

from myhdl import block
from myhdl._misc import _isGenSeq
from myhdl._Signal import _Signal


class HdlClass(ABC):
    '''
        This Abstract Base Class 
    '''

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    @block(skipname=True)
    def hdl(self, *args, **kwargs):
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
        # THIS doesn't look that great - the Simulator will show an intermediate block (this one)
        # as 'None', and that really doesn't look nice
        # BUT we have handled that in _tracesignals.py

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

    def convert(self, **kwargs):
        if hasattr(self, '_hdlb'):
            # reset _driven attribute to avoid a '*Signal has multiple drivers: *' **fatal** error
            # when converting for successive V* (as shown in test_hdlclassxx.py
            for arg in self._hdlb.args:
                if isinstance(arg, _Signal):
                    arg._driven = False
        else:
            self._hdlb = self.hdl()
            ports = []
            for name, sig in self.__dict__.items():
                if isinstance(sig, _Signal):
                    if sig._name is None:
                        # print(f'  {name}:{repr(sig)}')
                        sig._name = name
                    ports.append(sig)
            self._hdlb.args = tuple(ports)

            # still need to get the names of the ports into argnames
            # but perhaps we can only do that in the converter?
            # yes: look at _AnalyzeTopFuncVisitor:visit_FunctionDef()
            # but ideally we should do ity here?

            # add an attribute to the block so other code can find out what we are
            self._hdlb.isHdlClass = True

        self._hdlb.convert(**kwargs)
