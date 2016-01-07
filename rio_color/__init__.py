import numpy as np

__version__ = '0.0.0'

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

def sigmoidal(arr, bias, contrast):

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

    return sigmoidal(rgb, bias, contrast)


def color_worker(srcs, window, ij, args):
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
