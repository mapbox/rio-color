import numpy as np
from .utils import epsilon


# Color manipulation functions
def sigmoidal(arr, contrast, bias):
    """
    Sigmoidal contrast is type of contrast control that
    adjusts the contrast without saturating highlights or shadows.
    It allows control over two factors:
    the contrast range from light to dark, and where the middle value
    of the mid-tones falls. The result is a non-linear and smooth
    contrast change.

    Parameters
    ----------
    contrast : integer
        Enhances the intensity differences between the lighter and darker
        elements of the image. For example, 0 is none, 3 is typical and
        20 is a lot.
    bias : float
        Threshold level for the contrast function to center on
        (typically centered at '50%')


    Notes
    ----------

    Sigmoidal contrast is based on the sigmoidal transfer function:

    .. math:: g(u) = ( 1/(1 + e^{- \alpha * u + \beta)})

    This sigmoid function is scaled so that the output is bound by
    the interval [0, 1].

    .. math:: ( 1/(1 + e^(\beta * (\alpha - u))) - 1/(1 + e^(\beta * \alpha)))/
        ( 1/(1 + e^(\beta*(\alpha - 1))) - 1/(1 + e^(\beta * \alpha)) )

    Where :math: `\alpha` is the threshold level, and :math: `\beta` the
    contrast factor to be applied.

    References
    ----------
    .. [CT] Hany Farid "Fundamentals of Image Processing"
            http://www.cs.dartmouth.edu/farid/downloads/tutorials/fip.pdf

    """
    alpha, beta = bias, contrast
    # We use the names a and b to match documentation.

    if alpha == 0:
        alpha = epsilon

    if beta == 0:
        return arr

    np.seterr(divide='ignore', invalid='ignore')

    if beta > 0:
        numerator = 1 / (1 + np.exp(beta * (alpha - arr))) - \
            1 / (1 + np.exp(beta * alpha))
        denominator = 1 / (1 + np.exp(beta * (alpha - 1))) - \
            1 / (1 + np.exp(beta * alpha))
        output = numerator / denominator

    else:
        # Inverse sigmoidal function:
        # todo: account for 0s
        # todo: formatting ;)
        output = (
            (beta * alpha) - np.log(
                (
                    1 / (
                        (arr / (1 + np.exp(beta * alpha - beta))) -
                        (arr / (1 + np.exp(beta * alpha))) +
                        (1 / (1 + np.exp(beta * alpha)))
                    )
                ) - 1)
            ) / beta

    if np.any(output < 0) or np.any(output > (1 + epsilon)):
        raise ValueError("Output is not within the range of [0,1]")
    else:
        return output


def gamma(arr, g):
    """
    Gamma correction is a nonlinear operation that
    adjusts the image's channel values pixel-by-pixel according
    to a power-law:

    .. math:: pixel_{out} = pixel_{in} ^ {\gamma}

    Setting gamma (:math:`\gamma`) to be less than 1.0 darkens the image and
    setting gamma to be greater than 1.0 lightens it.

    Parameters
    ----------
    gamma (:math:`\gamma`): float
        Reasonable values range from 0.8 to 2.3.


    """
    return arr**(1.0 / g)


def saturation(arr, percent):
    """
    Multiply saturation by percent in LCH color space to adjust the intensity
    of color in the image. As saturation increases, colors appear
    more "pure." As saturation decreases, colors appear more "washed-out."

    Parameters
    ----------
    percent: integer

    """
    img = rgb2lch(arr)
    # Adjust chroma, band at index=1
    img[1] = img[1] * (percent / 100.0)
    return lch2rgb(img)


# Utility functions
def rgb2lch(rgb):
    """
    Converts image array from RGB to LCH color space
    """
    from skimage.color import rgb2lab, lab2lch
    # reshape for skimage (bands, cols, rows) -> (cols, rows, bands)
    srgb = np.swapaxes(rgb, 0, 2)
    # convert colorspace
    lch = lab2lch(rgb2lab(srgb))
    # return in (bands, cols, rows) order
    return np.swapaxes(lch, 2, 0)


def lch2rgb(lch):
    """
    Converts image array from LCH color space to RGB
    """
    from skimage.color import lch2lab, lab2rgb
    # reshape for skimage (bands, cols, rows) -> (cols, rows, bands)
    slch = np.swapaxes(lch, 0, 2)
    # convert colorspace
    rgb = lab2rgb(lch2lab(slch))
    # return in (bands, cols, rows) order
    return np.swapaxes(rgb, 2, 0)


def simple_atmo(rgb, haze, contrast, bias):
    '''
    A simple, static (non-adaptive) atmospheric correction function.

    Parameters
    ----------
    haze: float
        Amount of haze to adjust for. For example, 0.03
    contrast : integer
        Enhances the intensity differences between the lighter and darker
        elements of the image. For example, 0 is none, 3 is typical and
        20 is a lot.
    bias : float
        Threshold level for the contrast function to center on
        (typically centered at '50%')


    '''
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
                        "{} BAND must be between 1 and {}"
                        .format(opname, count))
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
