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

    """ rs232 configuration object.

    Attributes:
    baud_rate -- baud_rate in bits per second
    n_bits -- number of data bits: 7 or 8
    n_stops -- number of stop bits: 1 or 2
    parity -- parity configuration: None, ODD, EVEN, MARK or SPACE

    """
    
    __slots__ = ("baud_rate", "n_bits", "n_stops", "parity")

    def __init__(self, baud_rate=9600, n_bits=8, n_stops=1, parity=None):
        """ Return new Config object with actual or default parameters """
        self.baud_rate = baud_rate
        self.n_bits = n_bits
        self.n_stops = n_stops
        self.parity = parity
    

def parity(data, cfg):
    """ Return data parity as configured """
    if cfg == ODD:
        return not reduceXor(data[8:])
    elif cfg== EVEN:
        return reduceXor(data[8:])
    elif cfg == MARK:
        return 1
    elif cfg == SPACE:
        return 0

def reduceXor(bv):
    """ Return reduction xor of all bits in bv """
    return reduce(operator.xor, [b for b in bv])
 
