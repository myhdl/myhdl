from itertools import chain

import pytest

from myhdl.conversion import verify

xfail = pytest.mark.xfail

hdlmap = {
    'verilog': ('icarus', 'vlog'),
    'vhdl': ('GHDL', 'vcom')
}


def bug(issue_no, hdl='all'):
    if hdl == 'all':
        sims = list(chain.from_iterable(hdlmap.values()))
    else:
        sims = hdlmap[hdl]
    return xfail(verify.simulator in sims, reason='issue '+issue_no)
