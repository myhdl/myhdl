SLOW, MEDIUM, FAST = range(3)

BEHAVIOR, STRUCTURE = range(2)

def log2ceil(n):
    m = 0
    p = 1
    for i in range(n+1):
        if p < n:
            m += 1
            p *= 2
    return m
