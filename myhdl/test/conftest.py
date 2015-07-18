from itertools import chain

import pytest

from myhdl.conversion import analyze, verify

xfail = pytest.mark.xfail

hdlmap = {
    'verilog': ('iverilog', 'vlog', 'cver'),
    'vhdl': ('ghdl', 'vcom')
}

all_sims = list(chain.from_iterable(hdlmap.values()))


def pytest_addoption(parser):
    parser.addoption("--sim", action="store", choices=all_sims,
                     help="HDL Simulator")


def pytest_configure(config):
    sim = config.getoption('sim')
    if sim is not None:
        verify.simulator = analyze.simulator = sim


def pytest_report_header(config):
    if config.getoption('sim') is not None:
        return 'Simulator: '+verify.simulator


def bug(issue_no, hdl='all'):
    if hdl == 'all':
        sims = all_sims
    else:
        sims = hdlmap[hdl]
    return xfail(verify.simulator in sims, reason='issue '+issue_no)
