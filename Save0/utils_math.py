# Arrays
def flatten(x, y, ws):
    # Convert (x, y) to 1D index.
    return x + y * ws


def reshape(pos, ws):
    # Convert 1D index to (x, y).
    return pos % ws, pos // ws


# Next
def fibonacci(a, b):
    # Return next Fibonacci state (b, a+b).
    return b, a + b


def next_val(val):
    # Return val increased.
    return val * 2
