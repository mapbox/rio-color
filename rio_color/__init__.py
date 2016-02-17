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


def saturation(arr, percent):
    """
    multiply saturation by percent in LCH color space
    """
    lch = rgb2lch(arr)
    # Adjust chroma, band at index=1
    lch[1] = lch[1] * (percent / 100.0)
    return lch2rgb(lch)


def rgb2lch(rgb):
    from skimage.color import rgb2lab, lab2lch
    # reshape for skimage (bands, cols, rows) -> (cols, rows, bands)
    srgb = np.swapaxes(rgb, 0, 2)
    # convert colorspace
    lch = lab2lch(rgb2lab(srgb))
    # return in (bands, cols, rows) order
    return np.swapaxes(lch, 2, 0)


def lch2rgb(lch):
    from skimage.color import lch2lab, lab2rgb
    # reshape for skimage (bands, cols, rows) -> (cols, rows, bands)
    slch = np.swapaxes(lch, 0, 2)
    # convert colorspace
    rgb = lab2rgb(lch2lab(slch))
    # return in (bands, cols, rows) order
    return np.swapaxes(rgb, 2, 0)


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

    for func in parse_operations(args['operations'], arr.shape[0]):
        arr = func(arr)

    # scaled 0 to 1, now scale to outtype
    return scale_dtype(arr, args['out_dtype'])


def parse_operations(operations, count):
    """Takes an iterable of operations,
    each operation is expected to be a string with a specified syntax

    "OPERATION-NAME BANDS ARGS..."

    And yields a list of functions that take and return ndarrays
    """
    band_lookup = {'r': 1, 'g': 2, 'b': 3}

    opfuncs = {
        'saturation': saturation,
        'sigmoidal': sigmoidal,
        'gamma': gamma}

    opkwargs = {
        'saturation': ('percent',),
        'sigmoidal': ('contrast', 'bias'),
        'gamma': ('g',)}

    # Operations that assume RGB colorspace
    rgb_ops = ('saturation',)

    for op in operations:
        parts = op.split(" ")
        opname = parts[0]
        bandstr = parts[1]
        args = parts[2:]

        try:
            func = opfuncs[opname]
        except KeyError:
            raise ValueError("{} is not a valid operation".format(opname))

        if opname in rgb_ops:
            # ignore bands, assumed to be in rgb
            # push 2nd arg into args
            args = [bandstr] + args
            bands = (1, 2, 3)
        else:
            # 2nd arg is bands
            # parse r,g,b ~= 1,2,3
            bands = set()
            for bs in bandstr.split(","):
                try:
                    band = int(bs)
                except ValueError:
                    band = band_lookup[bs.lower()]
                if band < 1 or band > count:
                    raise ValueError(
                        "{} BAND must be between 1 and {}".format(opname, count))
                bands.add(band)

        # assume all args are float
        args = [float(arg) for arg in args]
        kwargs = dict(zip(opkwargs[opname], args))

        def f(arr):
            if opname in rgb_ops:
                # apply func to array assuming 3 band r,g,b
                arr = func(arr, **kwargs)
            else:
                # apply func to array band at a time
                for b in bands:
                    arr[b - 1] = func(arr[b - 1], **kwargs)
            return arr

        yield f
