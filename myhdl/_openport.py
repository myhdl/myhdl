'''
Created on 19 okt. 2023

@author: josy
'''

from myhdl._Signal import _Signal


class OpenPort(_Signal):
    ''' 
        helper for VHDL style 'open' ports
        This avoids warnings of outputs 'driven but not read' 
        both in the conversion process and 
        later in synthesis by the Vendor tool, although those warnings will be buried
        by the million ones coming from the Vendor IP ...
    '''

    # :code
    def __init__(self):
        ''' :
            OpenPort() has no arguments
        '''
        super(OpenPort, self).__init__(bool(0))
        self.__name = None
        self._read = True

    @property
    def _name(self):
        ''' rely on toVerilog to replace the VHDL comment operator '--' with '//' '''
        return '-- OpenPort ' + self.__name if self.__name else None

    @_name.setter
    def _name(self, name):
        self.__name = name

    @property
    def next(self):
        pass

    @next.setter
    def next(self, val):
        ''' discard any 'new' value '''
        pass

    # override the Signal.driven property
    @property
    def driven(self):
        pass

    @driven.setter
    def driven(self, val):
        pass

    @property
    def val(self):
        ''' an OpenPort object should not be read
            but it may feed another 'Open' object?
            returning 0 satisfies both bool() and intbv() 
        '''
        return 0


if __name__ == '__main__':
    pass
