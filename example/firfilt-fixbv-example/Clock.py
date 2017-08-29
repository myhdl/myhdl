
from __future__ import division

import myhdl
from myhdl import instance, delay

_clock_num = 0
_clock_list = []


class Clock(myhdl.SignalType):
    timescale = '1ns'

    def __init__(self, val, frequency=1):
        """
        This is a clock object, it is a thin wrapper around the
        myhdl.Signal object and provides needed attributes and
        clock generation (``gen``) for testbenches.
        Arguments:
            val: the initial value of the signal
            frequency (float): the frequency of this clock
        """
        global _clock_num, _clock_list
        self._frequency = frequency
        self._timescale = self.timescale
        self._period = 1/frequency
        self._set_hticks()
        self.clock_num = _clock_num
        _clock_num += 1
        super(Clock, self).__init__(bool(val))
        _clock_list.append(self)
        self.max_frequency = max(_clock_list)

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, f):
        self._frequency = f
        self._period = 1/f
        self._set_hticks()
        
    @property
    def period(self):
        return self._period

    @property
    def ticks(self):
        """
        Returns the number of simulation ticks that will elapse per clock tick.
        """
        return self._ticks

    def _set_hticks(self):
        # @todo: current limitation, the clock sim ticks are only
        #        valid for 1ns sim period.
        # self._nts = self._convert_timescale(self._timescale)
        self.timescale = "".join(self.timescale.split())

        self._nts = 1e-9
        self._hticks = int(round((self._period/self._nts)/2))
        assert self._hticks > 0
        self._ticks = self._hticks * 2

    def _convert_timescale(self, ts):
        # @todo: need to complete this, ts is in the form
        #        "[0-9]*["ms","us","ns","ps"], parse the text
        #        format and retrieve a numerical value
        # separate the numerical and text        
        nts = 1e9
        return nts

    @myhdl.block
    def gen(self, hticks=None):
        if hticks is None:
            hticks = self._hticks
        else:
            hticks = int(round(hticks))
            assert hticks > 0
            self._hticks = hticks
            self._ticks = hticks * 2

        @instance
        def gclock():
            self.next = False
            while True:
                yield delay(hticks)
                self.next = not self.val

        return gclock
