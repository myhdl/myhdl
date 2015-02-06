from __future__ import absolute_import, print_function
from myhdl.conversion import verify, analyze

verify.simulator = analyze.simulator = "vlog"
