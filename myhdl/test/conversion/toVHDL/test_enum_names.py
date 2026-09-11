import warnings

import pytest

from myhdl import block, always, Signal, enum, ToVHDLWarning


def enum_names_design(a_extra=(), b_extra=()):
    ''' Returns an instance using two enum types. The literals in `a_extra`
    and `b_extra` are added to the respective enum types so their names are
    checked on conversion; they are not used in the logic.
    '''
    t_a = enum('IDLE', 'RUN', *a_extra)
    t_b = enum('STOP', 'GO', *b_extra)

    @block
    def enum_names(clk, o):
        sa = Signal(t_a.IDLE)
        sb = Signal(t_b.STOP)

        @always(clk.posedge)
        def logic():
            if sa == t_a.IDLE:
                sa.next = t_a.RUN
            else:
                sa.next = t_a.IDLE
            if sb == t_b.STOP:
                sb.next = t_b.GO
            else:
                sb.next = t_b.STOP
            if sa == t_a.RUN and sb == t_b.GO:
                o.next = 1
            else:
                o.next = 0

        return logic

    return enum_names(Signal(bool(0)), Signal(bool(0)))


t_mode = enum('OFF', 'RUN', 'x')


@block
def enum_port_names(clk, mode, o):
    # t_mode is a port type, so is declared in a package rather than in the
    # architecture. Its literal 'x' clashes with the signal x.
    x = Signal(bool(0))

    @always(clk.posedge)
    def logic():
        if mode == t_mode.RUN:
            x.next = 1
        else:
            x.next = 0
        o.next = x

    return logic


def test_literal_shared_between_enum_types():
    # VHDL allows literals of different enum types to share a name
    a_block = enum_names_design(b_extra=('IDLE',))

    with warnings.catch_warnings():
        warnings.simplefilter('error', ToVHDLWarning)
        a_block.convert(hdl='VHDL')


def test_literal_shared_between_enum_types_analyze():
    assert enum_names_design(b_extra=('IDLE',)).analyze_convert() == 0


@pytest.mark.parametrize('a_extra, message', [
    (('wait',), "VHDL keyword used: wait"),
    (('_x',), "VHDL variable names cannot start with '_': _x"),
    (('Idle',), r"reused in namespace t_enum_t_a_\d+: Idle"),
    (('o',), r"Enum literal in namespace t_enum_t_a_\d+ clashes with a name "
             r"in root namespace: o"),
    (('sb',), r"Name clashes with an enum literal in namespace t_enum_t_a_\d+: "
              r"sb"),
    (('SB',), r"Name clashes with an enum literal in namespace t_enum_t_a_\d+: "
              r"sb"),
])
def test_invalid_enum_literal(a_extra, message):
    a_block = enum_names_design(a_extra=a_extra)

    with pytest.warns(ToVHDLWarning, match=message):
        a_block.convert(hdl='VHDL')


def test_port_enum_literal_clashes_with_signal():
    a_block = enum_port_names(
        Signal(bool(0)), Signal(t_mode.OFF), Signal(bool(0)))

    with pytest.warns(
            ToVHDLWarning,
            match=r"Name clashes with an enum literal in namespace "
                  r"t_enum_t_mode_\d+: x"):
        a_block.convert(hdl='VHDL')
