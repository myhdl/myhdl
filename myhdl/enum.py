from types import StringType


def enum(*args):

    args = list(args)
    # only default encoding for now
    argdict = {}
    encoding = {}
    i = 0
    for arg in args:
        if type(arg) is not StringType:
            raise TypeError
        if argdict.has_key(arg):
            raise ValueError
        argdict[i] = arg
        encoding[arg] = i
        i += 1
        
    class EnumItem(object):
        def __init__(self, arg):
            self._val = encoding[arg]
        def __repr__(self):
            return argdict[self._val]
        __str__ = __repr__

    class Enum(object):
        def __init__(self):
            for slot in args:
                self.__dict__[slot] = EnumItem(slot)
        def __setattr__(self, attr, val):
            raise AttributeError
        def __len__(self):
            return len(args)
        def __repr__(self):
            s = ""
            for arg in args:
                s += "%s=%d, " % (arg, encoding[arg])
            return "<Enum: %s>" % s[:-2]
        __str__ = __repr__
        
    return Enum()




    
        
