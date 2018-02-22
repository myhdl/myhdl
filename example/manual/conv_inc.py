from myhdl import toVerilog, toVHDL, Signal, ResetSignal, modbv
from inc import inc

ACTIVE_LOW, INACTIVE_HIGH = 0, 1


# conversion
m = 8

count = Signal(modbv(0)[m:])
enable = Signal(bool(0))
clock  = Signal(bool(0))
reset = ResetSignal(0, active=0, async=True)

inc_inst = inc(count, enable, clock, reset)
inc_inst = toVerilog(inc, count, enable, clock, reset)
inc_inst = toVHDL(inc, count, enable, clock, reset)
