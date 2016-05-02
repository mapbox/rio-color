import numpy as np
import re

# The type to be used for all intermediate math
# operations. Should be a float because values will
# be scaled to the range 0..1 for all work.

math_type = np.float64

epsilon = np.finfo(math_type).eps


def to_math_type(arr):
    """Convert an array from native integer dtype range to 0..1
    scaling down linearly
    """
    max_int = np.iinfo(arr.dtype).max
    return arr.astype(math_type) / max_int


def scale_dtype(arr, dtype):
    """Convert an array from 0..1 to dtype, scaling up linearly
    """
    max_int = np.iinfo(dtype).max
    return (arr * max_int).astype(dtype)


def magick_to_rio(convert_opts):
    """Translate a limited subset of imagemagick convert commands
    to rio color operations

    Parameters
    ----------
    convert_opts: String, imagemagick convert options

    Returns
    -------
    operations string, ordered rio color operations
    """
    ops = []
    bands = None

    def set_band(x):
        global bands
        if x.upper() == "RGB":
            x = "RGB"
        bands = x.upper()

    set_band("RGB")

    def append_sig(arg):
        global bands
        args = list(filter(None, re.split("[,x]+", arg)))
        if len(args) == 1:
            args.append(0.5)
        elif len(args) == 2:
            args[1] = float(args[1].replace("%", "")) / 100.0
        ops.append("sigmoidal {} {} {}".format(
            bands, *args))

    def append_gamma(arg):
        global bands
        ops.append("gamma {} {}".format(
            bands, arg))

    def append_sat(arg):
        args = list(filter(None, re.split("[,x]+", arg)))
        # ignore args[0]
        # convert to proportion
        prop = float(args[1]) / 100
        ops.append("saturation {}".format(prop))

    nextf = None
    for part in convert_opts.strip().split(" "):
        if part == "-channel":
            nextf = set_band
        elif part == "+channel":
            set_band("RGB")
            nextf = None
        elif part == "-sigmoidal-contrast":
            nextf = append_sig
        elif part == "-gamma":
            nextf = append_gamma
        elif part == "-modulate":
            nextf = append_sat
        else:
            if nextf:
                nextf(part)
            nextf = None

    return ' '.join(ops)
