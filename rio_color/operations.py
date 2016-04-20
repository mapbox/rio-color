import numpy as np
from .utils import epsilon

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
    img = rgb2lch(arr)
    # Adjust chroma, band at index=1
    img[1] = img[1] * (percent / 100.0)
    return lch2rgb(img)


# Utility functions
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


def simple_atmo(rgb, haze, contrast, bias):
    '''A simple, static (non-adaptive) atmospheric correction function.'''
    # bias assumed to be given in percent,
    # convert to proportion
    bias = bias / 100.0

    gamma_b = 1 - haze
    gamma_g = 1 - (haze * (1 / 3.0))

    rgb[1] = gamma(rgb[1], gamma_g)
    rgb[2] = gamma(rgb[2], gamma_b)

    return sigmoidal(rgb, contrast, bias)


def parse_operations(operations):
    """Takes an iterable of operations,
    each operation is expected to be a string with a specified syntax

    "OPERATION-NAME BANDS ARGS..."

    And yields a list of functions that take and return ndarrays
    """
    band_lookup = {'r': 1, 'g': 2, 'b': 3}
    count = len(band_lookup)

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

        def f(arr, func=func, kwargs=kwargs):
            # Avoid mutation by copying
            newarr = arr.copy()
            if opname in rgb_ops:
                # apply func to array's first 3 bands, assumed r,g,b
                # additional band(s) are untouched
                newarr[0:3] = func(newarr[0:3], **kwargs)
            else:
                # apply func to array band at a time
                for b in bands:
                    newarr[b - 1] = func(arr[b - 1], **kwargs)
            return newarr

        yield f
