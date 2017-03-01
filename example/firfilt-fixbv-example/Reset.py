
import myhdl
from myhdl import delay


class Reset(myhdl.ResetSignal):
    def __init__(self, val, active, async):
        """ Reset signal
        This is a thin wrapper around the myhdl.ResetSignal to
        provide the generator ``pulse`` that is often used in
        testbenches.
        Arguments:
            val (int, bool): default value of the reset signal
            active (int, bool): active state, when is reset active
            async (bool): asynchronous reset or not
        """
        super(Reset, self).__init__(val, active, async)

    def pulse(self, delays=10):
        if isinstance(delays, int):
            self.next = self.active
            yield delay(delays)
            self.next = not self.active
        elif isinstance(delays, tuple):
            assert len(delays) in (1, 2, 3), "Incorrect number of delays"
            self.next = not self.active if len(delays) == 3 else self.active
            for dd in delays:
                yield delay(dd)
                self.next = not self.val
            self.next = not self.active
        else:
            raise ValueError("{} type not supported".format(type(delays)))
