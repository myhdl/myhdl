from myhdl import intbv
concat = intbv.concat # shorthand

COSET = 0x55

def calculateHec(header):
    """ Return hec for an ATM header, represented as an intbv.
    """
    hec = intbv(0)
    for bit in header[32:]:
        hec[8:] = concat(hec[7:2],
                         bit ^ hec[1] ^ hec[7],
                         bit ^ hec[0] ^ hec[7],
                         bit ^ hec[7]
                        )
    return hec ^ COSET


headers = ( 0x00000000,
            0x01234567,
            0xbac6f4ca
          )

if __name__ == '__main__':
    for header in headers:
        print hex(calculateHec(intbv(header)))
        
