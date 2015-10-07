import pytest


class raises_kind(object):
    def __init__(self, exc, kind):
        self.exc = exc
        self.kind = kind

    def __enter__(self):
        return None

    def __exit__(self, *tp):
        __tracebackhide__ = True
        if tp[0] is None:
            pytest.fail("DID NOT RAISE")
        assert tp[1].kind == self.kind
        return issubclass(tp[0], self.exc)
