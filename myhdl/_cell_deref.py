
# cell dereferencing hack, thanks to Samuele Pedroni

from types import FunctionType

def _proto_acc(v=None):
    def acc():
        return v
    return acc

_acc0 = _proto_acc()

_make_acc = lambda cell: (FunctionType(_acc0.__code__,
                                        _acc0.__globals__,
                                        '#cell_acc',
                                        _acc0.__defaults__,
                                        (cell,)
                                        )
                          )

def _cell_deref(cell):
    return _make_acc(cell)()
