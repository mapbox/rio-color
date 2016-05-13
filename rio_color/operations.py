import numpy as np
from .utils import epsilon
from .colorspace import saturate_rgb


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
    arr : ndarray, float, 0 .. 1
        Array of color values to adjust
    contrast : integer
        Enhances the intensity differences between the lighter and darker
        elements of the image. For example, 0 is none, 3 is typical and
        20 is a lot.
    bias : float, between 0 and 1
        Threshold level for the contrast function to center on
        (typically centered at 0.5)

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
    if (arr.max() > 1.0 + epsilon) or (arr.min() < 0 - epsilon):
        raise ValueError("Input array must have float values between 0 and 1")

    if (bias > 1.0 + epsilon) or (bias < 0 - epsilon):
        raise ValueError("bias must be a scalar float between 0 and 1")

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
    output = arr**(1.0 / g)

    if np.any(output < 0) or np.any(output > (1 + epsilon)):
        raise ValueError("Gamma corrected output is not within the range of [0,1]")
    elif np.isnan(output.sum()):
        raise ValueError("Gamma corrected output contains NaN")
    else:
        return output


def saturation(arr, proportion):
    """Apply saturation to an RGB array (in LCH color space)

    Multiply saturation by proportion in LCH color space to adjust the intensity
    of color in the image. As saturation increases, colors appear
    more "pure." As saturation decreases, colors appear more "washed-out."

    Parameters
    ----------
    arr: ndarray with shape (3, ..., ...)
    proportion: number

    """
    if arr.shape[0] != 3:
        raise ValueError("saturation requires a 3-band array")
    return saturate_rgb(arr, proportion)


def simple_atmo_opstring(haze, contrast, bias):
    gamma_b = 1 - haze
    gamma_g = 1 - (haze / 3.0)
    ops = ("gamma g {gamma_g}, "
           "gamma b {gamma_b}, "
           "sigmoidal rgb {contrast} {bias}").format(
               gamma_g=gamma_g, gamma_b=gamma_b,
               contrast=contrast, bias=bias)
    return ops


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
    bias : float, between 0 and 1
        Threshold level for the contrast function to center on
        (typically centered at 0.5 or 50%)
    '''
    gamma_b = 1 - haze
    gamma_g = 1 - (haze / 3.0)
    arr = np.empty(shape=(3, rgb.shape[1], rgb.shape[2]))

    arr[0] = rgb[0]
    arr[1] = gamma(rgb[1], gamma_g)
    arr[2] = gamma(rgb[2], gamma_b)

    output = rgb.copy()
    output[0:3] = sigmoidal(arr, contrast, bias)

    return output

def _op_factory(func, kwargs, opname, bands, rgb_op=False):
    """create an operation function closure
    don't call directly, use parse_operations
    returns a function which itself takes and returns ndarrays
    """
    def f(arr):
        # Avoid mutation by copying
        newarr = arr.copy()
        if rgb_op:
            # apply func to array's first 3 bands, assumed r,g,b
            # additional band(s) are untouched
            newarr[0:3] = func(newarr[0:3], **kwargs)
        else:
            # apply func to array band at a time
            for b in bands:
                newarr[b - 1] = func(arr[b - 1], **kwargs)
        return newarr

    f.__name__ = str(opname)
    return f


def parse_operations(ops_string):
    """Takes a string of operations written with a handy DSL

    "OPERATION-NAME BANDS ARG1 ARG2 OPERATION-NAME BANDS ARG"

    And returns a list of functions, each of which take and return ndarrays
    """
    band_lookup = {'r': 1, 'g': 2, 'b': 3}
    count = len(band_lookup)

    opfuncs = {
        'saturation': saturation,
        'sigmoidal': sigmoidal,
        'gamma': gamma}

    opkwargs = {
        'saturation': ('proportion',),
        'sigmoidal': ('contrast', 'bias'),
        'gamma': ('g',)}

    # Operations that assume RGB colorspace
    rgb_ops = ('saturation',)

    # split into tokens, commas are optional whitespace
    tokens = [x.strip() for x in ops_string.replace(',', '').split(' ')]
    operations = []
    current = []
    for token in tokens:
        if token.lower() in opfuncs.keys():
            if len(current) > 0:
                operations.append(current)
                current = []
        current.append(token.lower())
    if len(current) > 0:
        operations.append(current)

    result = []
    for parts in operations:
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
            for bs in bandstr:
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

        # Create opperation function
        f = _op_factory(func=func, kwargs=kwargs, opname=opname,
                        bands=bands, rgb_op=(opname in rgb_ops))
        result.append(f)

    return result
