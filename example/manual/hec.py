from myhdl import intbv, concat

COSET = 0x55

def calculateHec(header):
    """ Return hec for an ATM header, represented as an intbv.

    The hec polynomial is 1 + x + x**2 + x**8.
    """
    hec = intbv(0)
    for bit in header[32:]:
        hec[8:] = concat(hec[7:2],
                         bit ^ hec[1] ^ hec[7],
                         bit ^ hec[0] ^ hec[7],
                         bit ^ hec[7]
                        )
    return hec ^ COSET


headers = ( 0x00000000L,
            0x01234567L,
            0xbac6f4caL
          )

def main():
    for header in headers:
        print hex(calculateHec(intbv(header)))
        
if __name__ == '__main__':
    main()
