# cell dereferencing hack, thanks to Samuele Pedroni

import new

def _proto_acc(v=None):
    def acc():
        return v
    return acc

_acc0 = _proto_acc()

_make_acc = lambda cell: (new.function (_acc0.func_code,
                                        _acc0.func_globals,
                                        '#cell_acc',
                                        _acc0.func_defaults,
                                        (cell,)
                                        )
                          )

def _cell_deref(cell):
    return _make_acc(cell)()
