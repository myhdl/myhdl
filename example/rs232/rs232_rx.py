import myhdl
from myhdl import *

from rs232_util import sec, parity, ParityError, StopBitError

def rs232_rx(rx, actual, cfg):
    
    """ rs232 receiver.

    rx -- serial input data
    actual -- data actually received
    cfg -- rs232_util.Config configuration object

    """
    
    @instance
    def logic():
        data = intbv(0)
        period = int(1*sec / cfg.baud_rate)

        yield rx.posedge
        yield delay(period // 2)

        data[7] = 0
        for i in downrange(cfg.n_bits):
            yield delay(period)
            data[i] = rx

        if cfg.parity is not None:
            yield delay(period)
            if rx != parity(data, cfg.parity):
                raise ParityError

        yield delay(period)
        if rx != 0:
            raise StopBitError

        actual[8:] = data

    return logic
        
    
