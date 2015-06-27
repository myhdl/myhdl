from contextlib import contextmanager

import pytest


@contextmanager
def raises_kind(exc, kind):
    with pytest.raises(exc) as excinfo:
        yield
    assert excinfo.value.kind == kind
