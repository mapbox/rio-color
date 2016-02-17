import numpy as np

__version__ = '0.1'

# The type to be used for all intermediate math
# operations. Should be a float because values will
# be scaled to the range 0..1 for all work.
math_type = np.float32

epsilon = np.finfo(math_type).eps


def to_math_type(arr, dtype):
    '''Convert an array from uint16 to 0..1, scaling down linearly'''
    max_int = np.iinfo(dtype).max
    return arr.astype(math_type) / max_int


def scale_dtype(arr, dtype):
    '''Convert an array from 0..1 to uint16, scaling up linearly'''
    max_int = np.iinfo(dtype).max
    return (arr * max_int).astype(dtype)


# Color manipulation functions

def sigmoidal(arr, contrast, bias):

    alpha, beta = bias, contrast
    # We use the names a and b to match documentation.

    if alpha == 0:
        alpha = epsilon

    if beta == 0:
        return arr

    np.seterr(divide='ignore', invalid='ignore')

    if beta > 0:
        # Forward sigmoidal function:
        # (This is really badly documented in the wild/internet.
        # @virginiayung is the only person I trust to understand it.)
        numerator = 1 / (1 + np.exp(beta * (alpha - arr))) - \
            1 / (1 + np.exp(beta * alpha))
        denominator = 1 / (1 + np.exp(beta * (alpha - 1))) - \
            1 / (1 + np.exp(beta * alpha))
        return numerator / denominator
    else:
        # Inverse sigmoidal function:
        # todo: account for 0s
        # todo: formatting ;)
        return (
            (beta * alpha) - np.log(
                (
                    1 / (
                        (arr / (1 + np.exp(beta * alpha - beta)))
                        - (arr / (1 + np.exp(beta * alpha)))
                        + (1 / (1 + np.exp(beta * alpha)))
                    )
                )
                - 1)
        ) / beta


def gamma(arr, g):
    return arr**(1.0 / g)


# Utility functions

def simple_atmo(rgb, haze, contrast, bias):
    '''A simple, static (non-adaptive) atmospheric correction function.'''

    gamma_b = 1 - haze
    gamma_g = 1 - (haze * (1 / 3.0))

    rgb[1] = gamma(rgb[1], gamma_g)
    rgb[2] = gamma(rgb[2], gamma_b)

    return sigmoidal(rgb, contrast, bias)


# Rio workers

def atmos_worker(srcs, window, ij, args):
    src = srcs[0]
    rgb = src.read(window=window)
    rgb = to_math_type(rgb, rgb.dtype)

    atmos = simple_atmo(
        rgb,
        args['atmo'],
        args['contrast'],
        args['bias'])

    # should be scaled 0 to 1, scale to outtype
    return scale_dtype(atmos, args['out_dtype'])


def color_worker(srcs, window, ij, args):
    src = srcs[0]
    arr = src.read(window=window)
    arr = to_math_type(arr, arr.dtype)

    for func in parse_operations(args['operations']):
        arr = func(arr)

    # scaled 0 to 1, now scale to outtype
    return scale_dtype(arr, args['out_dtype'])


def parse_operations(operations):
    """Takes an iterable of operations,
    each operation is expected to be a string with a specified syntax

    "OPERATION-NAME BANDS ARGS..."

    And yields a list of functions that take and return ndarrays
    """
    band_lookup = {'r': 1, 'g': 2, 'b': 3}
    opfuncs = {
        'sigmoidal': sigmoidal,
        'gamma': gamma}
    opkwargs = {
        'sigmoidal': ('contrast', 'bias'),
        'gamma': ('g')}

    for op in operations:
        parts = op.split(" ")
        opname = parts[0]
        bandstr = parts[1]
        args = parts[2:]

        func = opfuncs[opname]

        # parse bands, r,g,b ~= 1,2,3
        bands = set()
        for bs in bandstr.split(","):
            try:
                band = int(bs)
            except ValueError:
                band = band_lookup[bs.lower()]
            bands.add(band)

        # assume all args are float
        args = [float(arg) for arg in args]
        kwargs = dict(zip(opkwargs[opname], args))

        def f(arr):
            # apply func to array band at a time
            for b in bands:
                arr[b - 1] = func(arr[b - 1], **kwargs)
            return arr

        yield f
