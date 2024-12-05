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

        frame = inspect.currentframe()
        loi = []
        try:
            outerframes = inspect.getouterframes(frame)
            dlocals = outerframes[3][0].f_locals
            keys = dlocals.keys()
            values = dlocals.values()

            # first resolve the ForwardPorts (if any)
            for value in values:
                if isinstance(value, list):
                    if len(value):
                        if isinstance(value[0], HdlClass):
                            for item in value:
                                refs = vars(item)
                                for dest, sig in refs.items():
                                    if isinstance(sig, ForwardPort):
                                        item.__setattr__(dest, getattr(dlocals[sig.hdlblock], sig.port))

                elif isinstance(value, HdlClass):
                    if id(value) != id(self):
                        refs = vars(value)
                        for dest, sig in refs.items():
                            if isinstance(sig, ForwardPort):
                                value.__setattr__(dest, getattr(dlocals[sig.hdlblock], sig.port))

                else:
                    pass

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
                        thdl.name = '{}'.format(key)
                        loi.append(thdl)

                # note that the always_xxx generators are also in keys/values
                elif _isGenSeq(value):
                    # just use the instance name
                    loi.append(value)

                else:
                    pass

        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

        del frame

        return loi

# ToDo ???
# None these work
#     def convert(self, **kwargs):
#         hchdl = self.hdl()
#         hchdl.convert(**kwargs)
#
#
# # helper routine
# @block
# # def wrapper(hdlclass, *args, **kwargs):
# def wrapper(*args, **kwargs):
#     # create the module
#     # print(f'{args=}')
#     # for arg in args:
#     #     print(f'{arg=}')
#
#     hc = args[0](*args[1:], **kwargs)
#     # print(f'{vars(hc)=}')
#     # get the block
#     hdlinstance = hc.hdl()
#     # hdlinstance.name = hc.__class__.__name__
#     # print(f'{vars(hdlinstance)=}')
#
#     return hdlinstance
#
#
# def convert(wrapper, **kwargs):
#     '''
#         this allows us to convert a class design without
#         having to write a wrapper
#     '''
#
#     # now convert for real
#     wrapper.convert(**kwargs)

