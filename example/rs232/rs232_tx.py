import operator

import myhdl
from myhdl import *

from rs232_util import reduceXor, sec, ODD, EVEN, MARK, SPACE

def rs232_tx(tx, data, cfg):

    """ rs232 transmitter.

    tx -- serial output data
    data -- input data byte to be transmitted
    cfg -- rs232_util.Config configuration object

    """
    
    duration = delay(int(1*sec / cfg.baud_rate))
    
    @instance
    def logic():
        tx.next = 1
        yield duration

        for i in downrange(cfg.n_bits):
            tx.next = data[i]
            yield duration

        if cfg.parity is not None:
            if cfg.n_bits == 7:
                data[7] = 0
            if cfg.parity == ODD:
                tx.next = not reduceXor(data[8:])
            elif cfg.parity == EVEN:
                tx.next = reduceXor(data[8:])
            elif cfg.parity == MARK:
                tx.next = 1
            elif cfg.parity == SPACE:
                tx.next = 0
            yield duration

        tx.next = 0
        for i in range(cfg.n_stops):
            yield duration

    return logic
    
    
