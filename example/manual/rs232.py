from __future__ import generators

from random import randrange

from myhdl import Signal, Simulation, StopSimulation, \
                  intbv, delay, negedge, join

DURATION_9600 = int(1e9 / 9600)

def rs232_tx(tx, data, duration=DURATION_9600):
    
    """ Simple rs232 transmitter procedure.

    tx -- serial output data
    data -- input data byte to be transmitted
    duration -- transmit bit duration
    
    """

    print 'TX: start bit'      
    tx.next = 0
    yield delay(duration)

    for i in range(8):
        print 'TX: %s' % data[i]
        tx.next = data[i]
        yield delay(duration)

    print 'TX: stop bit'       
    tx.next = 1
    yield delay(duration)

    
        
def rs232_rx(rx, data, duration=DURATION_9600, timeout=None):
    
    """ Simple rs232 receiver procedure.

    rx -- serial input data
    data -- data received
    duration -- receive bit duration
    
    """

    # wait on start bit, possibly with a timeout
    if timeout:
        yield negedge(rx), delay(timeout)
        if rx == 1:
            raise StopSimulation, "Time out error"
    else:
        yield negedge(rx)

    # sample in the middle
    yield delay(duration // 2)
    print 'RX: start bit'

    # receive data bits
    for i in range(8):
        yield delay(duration)
        print 'RX: %s' % rx
        data[i] = rx

    # stop bit
    yield delay(duration)
    print 'RX: stop bit'




def test1():
    tx = Signal(1)
    for i in range(1, 5):
        print "-- Call %s --" % i
        txData = intbv(randrange(2**8))
        yield rs232_tx(tx, txData)

        
def test2():
    tx = Signal(1)
    rx = Signal(1)
    rxData = intbv(0)
    txData = intbv(randrange(2**8))
    yield rs232_rx(rx, rxData, timeout=3*DURATION_9600-1), rs232_tx(tx, txData)
    

def test3():
    tx = Signal(1)
    rx = tx
    rxData = intbv(0)
    txData = intbv(randrange(2**8))
    yield rs232_rx(rx, rxData), rs232_tx(tx, txData)
    # yield rs232_rx(rx, rxData), rs232_tx(tx, txData)
    # yield join(rs232_rx(rx, rxData), rs232_tx(tx, txData))

Simulation(test1()).run()
print
Simulation(test2()).run()
print
Simulation(test3()).run()
    
