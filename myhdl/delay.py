""" delay class for use in yield statements """

_errmsg = "arg of delay constructor should be a positive int"

class delay(object):
    def __init__(self, val):
##         if type(val) != int or val < 1:
##             raise TypeError, _errmsg
        self._time = val

    def __nonzero__(self):
        if self._time:
            return 1
        return 0

