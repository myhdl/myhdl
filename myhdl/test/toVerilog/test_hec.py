import os
path = os.path
import unittest
from random import randrange

from myhdl import *

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


def HecCalculator(hec, header):
    h = intbv(0)[8:]
    while 1:
        yield header
        h[:] = 0
        for i in downrange(len(header)):
            bit = header[i]
            h[:] = concat(h[7:2],
                          bit ^ h[1] ^ h[7],
                          bit ^ h[0] ^ h[7],
                          bit ^ h[7]
                          )
        hec.next = h ^ COSET
        
objfile = "heccalc.o"           
analyze_cmd = "iverilog -o %s heccalc_inst.v tb_heccalc_inst.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
        
def HecCalculator_v(hec, header):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())

hec = Signal(intbv(0)[8:])
hec_v = Signal(intbv(0)[8:])
header = Signal(intbv(-1)[32:])

heccalc_inst = toVerilog(HecCalculator, hec, header)
# heccalc_inst = HecCalculator(hec, header)
heccalc_v_inst = HecCalculator_v(hec_v, header)


headers = [ 0x00000000L,
            0x01234567L,
            0xbac6f4caL
          ]

headers.extend([randrange(2**32-1) for i in range(10)])

class TestHec(unittest.TestCase):

    def stimulus(self):
        for h in headers:
            header.next = h
            yield delay(10)
            print "hec: %s hec_v: %s" % (hex(hec), hex(hec_v))
            self.assertEqual(hec, hec_v)

    def test(self):
        sim = self.stimulus(), heccalc_inst, heccalc_v_inst
        Simulation(sim).run()

        
if __name__ == '__main__':
    unittest.main()
