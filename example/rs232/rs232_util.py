import operator

sec = 1e9

ODD, EVEN, MARK, SPACE = range(4)

class Error(Exception):
    pass

class ParityError(Error):
    pass

class StopBitError(Error):
    pass

class Config(object):
    
    __slots__ = ("baud_rate", "n_bits", "n_stops", "parity")

    def __init__(self, baud_rate=9600, n_bits=8, n_stops=1, parity=None):
        self.baud_rate = baud_rate
        self.n_bits = n_bits
        self.n_stops = n_stops
        self.parity = parity
    

def parity(data, cfg):
    if cfg == ODD:
        return not reduceXor(data[8:])
    elif cfg== EVEN:
        return reduceXor(data[8:])
    elif cfg == MARK:
        return 1
    elif cfg == SPACE:
        return 0

def reduceXor(bv):
    return reduce(operator.xor, [b for b in bv])
 
