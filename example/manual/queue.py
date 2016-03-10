from __future__ import generators

import myhdl
from myhdl import *

def trigger(event):
    event.next = not event

class queue:
    def __init__(self):
       self.l = []
       self.sync = Signal(0)
       self.item = None
    def put(self,item):
       # non time-consuming method
       self.l.append(item)
       trigger(self.sync)
    def get(self):
       # time-consuming method
       if not self.l:
          yield self.sync
       self.item = self.l.pop(0)


q = queue()

def Producer(q):
    yield delay(120)
    for i in range(5):
        print "%s: PUT item %s" % (now(), i)
        q.put(i)
        yield delay(max(5, 45 - 10*i))

def Consumer(q):
    yield delay(100)
    while 1:
        print "%s: TRY to get item" % now()
        yield q.get()
        print "%s: GOT item %s" % (now(), q.item)
        yield delay(30)

def main():
    P = Producer(q)
    C = Consumer(q)
    sim = Simulation(P, C)
    sim.run()
    

if __name__ == '__main__':
    main()
