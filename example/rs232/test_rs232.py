from __future__ import generators
import sys
from random import randrange
import unittest
from unittest import TestCase

from rs232_rx import rs232_rx
from myhdl import Simulation, Signal, intbv, join

from rs232_tx import rs232_tx
from rs232_util import Config, EVEN, ODD, ParityError, Error

class rs232Test(TestCase):

    def default(self):
        tx = Signal(intbv(0))
        rx = tx
        actual = intbv(0)
        cfg = Config()
        for i in range(256):
            data = intbv(i)
            yield join(rs232_tx(tx, data, cfg), rs232_rx(rx, actual, cfg))
            self.assertEqual(data, actual)

    def testDefault(self):
        Simulation(self.default()).run(quiet=1)


    def oddParity(self):
        tx = Signal(intbv(0))
        rx = tx
        actual = intbv(0)
        cfg = Config(parity=ODD)
        for i in range(256):
            data = intbv(i)
            yield join(rs232_tx(tx, data, cfg), rs232_rx(rx, actual, cfg))
            self.assertEqual(data, actual)
        
    def testOddParity(self):
        Simulation(self.oddParity()).run(quiet=1)

    def sevenBitsEvenParity(self):
        tx = Signal(intbv(0))
        rx = tx
        actual = intbv(0)
        cfg = Config(parity=EVEN, n_bits=7)
        cfg_rx = Config(parity=EVEN, n_bits=7)
        for i in range(256):
            data = intbv(i)
            yield join(rs232_tx(tx, data, cfg), rs232_rx(rx, actual, cfg_rx))
            self.assertEqual(data, actual)
        
    def testSevenBitsEvenParity(self):
        Simulation(self.sevenBitsEvenParity()).run(quiet=1)
        
    def ParityError(self):
        tx = Signal(intbv(0))
        rx = tx
        actual = intbv(0)
        cfg_rx = Config(parity=ODD)
        cfg_tx = Config(parity=EVEN)
        data = intbv(randrange(256))
        yield join(rs232_tx(tx, data, cfg_tx), rs232_rx(rx, actual, cfg_rx))
        self.assertEqual(data, actual)
            
    def testParityError(self):
        try:
            Simulation(self.ParityError()).run(quiet=1)
        except ParityError:
            pass
        else:
            self.fail("Expected parity error")


class rs232Characterize(TestCase):

    def bench(self, tx_baud_rate):
        tx = Signal(intbv(0))
        rx = tx
        actual = intbv(0)
        cfg_tx = Config(baud_rate=tx_baud_rate)
        cfg_rx = Config()
        for i in range(256):
            data = intbv(i)
            yield join(rs232_tx(tx, data, cfg_tx), rs232_rx(rx, actual, cfg_rx))
            if not data == actual:
                raise Error

    def testCharacterize(self):
        coarseOffset = 100
        fineOffset = 5
        tx_baud_rate = 9600
        try:
            while 1:
                tx_baud_rate += coarseOffset
                Simulation(self.bench(tx_baud_rate)).run(quiet=1)
        except Error:
            pass
        while 1:
            try:
                tx_baud_rate -= fineOffset
                Simulation(self.bench(tx_baud_rate)).run(quiet=1)
            except Error:
                continue
            else:
                print "Max tx baudrate: %s" % tx_baud_rate
                break
        tx_baud_rate = 9600
        try:
            while 1:
                tx_baud_rate -= coarseOffset
                Simulation(self.bench(tx_baud_rate)).run(quiet=1)
        except Error:
            pass
        while 1:
            try:
                tx_baud_rate += fineOffset
                Simulation(self.bench(tx_baud_rate)).run(quiet=1)
            except Error:
                continue
            else:
                print "Min tx baudrate: %s" % tx_baud_rate
                break

                
if __name__ == "__main__":
    testRunner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=testRunner)
       

        
        

        
        


        

    
