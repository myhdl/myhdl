from __future__ import generators

from myhdl import delay, posedge, intbv, downrange

from rs232_util import sec, parity, ParityError, StopBitError

def rs232_rx(rx, actual, cfg):
    
    """ rs232 receiver.

    rx -- serial input data
    actual -- data actually received
    cfg -- rs232_util.Config configuration object

    """
    
    data = intbv(0)
    period = int(1*sec / cfg.baud_rate)
    
    yield posedge(rx)
    yield delay(period / 2)
    
    data[7] = 0
    for i in downrange(cfg.n_bits):
        yield delay(period)
        data[i] = rx.val
        
    if cfg.parity is not None:
        yield delay(period)
        if rx != parity(data, cfg.parity):
            raise ParityError
        
    yield delay(period)
    if rx != 0:
        raise StopBitError
    
    actual[8:] = data
        
    
