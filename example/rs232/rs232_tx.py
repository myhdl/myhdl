from __future__ import generators
import operator

from myhdl import Signal, downrange, delay, posedge

from rs232_util import sec, ODD, EVEN, MARK, SPACE

def rs232_tx(tx, data, cfg):
    
    duration = delay(int(1*sec / cfg.baud_rate))
    
    tx.next = 1
    yield duration
    
    for i in downrange(cfg.n_bits):
        tx.next = data[i]
        yield duration
        
    if cfg.parity is not None:
        if cfg.n_bits == 7:
            data[7] = 0
        if cfg.parity == ODD:
            tx.next = not reduce(operator.xor, [b for b in data[8:]])
        elif cfg.parity == EVEN:
            tx.next = reduce(operator.xor, [b for b in data[8:]])
        elif cfg.parity == MARK:
            tx.next = 1
        elif cfg.parity == SPACE:
            tx.next = 0
        yield duration
        
    tx.next = 0
    for i in range(cfg.n_stops):
        yield duration
    
    
