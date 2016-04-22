import numpy as np
import math


def rgb_to_lch(r, g, b, simplified=True, h_degrees=True):
    """Convert RGB colors to LCH

    Parameters
    ----------
    r: float
        0 to 1, Red
    g: float
        0 to 1, Blue
    b: float
        0 to 1, Blue
    simplified: boolean
        Use simplified RGB with gamma 2.2 (default, True)
        or the conditional linear adjustment for sRGB (False)
    h_degrees: boolean
        Return Hue in degrees (default, True)
        or radians in domain [-pi to pi] (False)

    Returns
    -------
    L, C, H tuple (Lightness, Chroma, Hue)
    """
    # convert RGB to linear scale
    if simplified:
        # Use gamma = 2.2, "simplified sRGB"
        rl = r ** 2.2
        gl = g ** 2.2
        bl = b ** 2.2
    else:
        # conditional sRGB linear adjustment
        if r < 0.04045:
            rl = r / 12.92
        else:
            rl = ((r + 0.055) / 1.055) ** 2.4

        if g < 0.04045:
            gl = g / 12.92
        else:
            gl = ((g + 0.055) / 1.055) ** 2.4

        if b < 0.04045:
            bl = b / 12.92
        else:
            bl = ((b + 0.055) / 1.055) ** 2.4

    # matrix mult for srgb->xyz,
    # includes adjustment for d65 reference white
    x = ((rl * 0.4124) + (gl * 0.3576) + (bl * 0.1805)) / 0.95047
    y = ((rl * 0.2126) + (gl * 0.7152) + (bl * 0.0722))
    z = ((rl * 0.0193) + (gl * 0.1192) + (bl * 0.9505)) / 1.08883

    # convert XYZ to LAB colorspace
    delta = 0.13793103448275862   # 6/29
    t0 = 0.008856451679035631  # (delta)^3
    alpha = 7.787037037037035  # 1/3 sqrt delta

    if x > t0:
        fx = x ** 0.333333333
    else:
        fx = (alpha * x) + delta

    if y > t0:
        fy = y ** 0.333333333
    else:
        fy = (alpha * y) + delta

    if z > t0:
        fz = z ** 0.333333333
    else:
        fz = (alpha * z) + delta

    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    C = ((a * a) + (b * b)) ** 0.5

    if h_degrees:
        H = math.degrees(math.atan2(b, a))
    else:
        H = math.atan2(b, a)

    return L, C, H


def lch_to_rgb(L, C, H, simplified=True, h_degrees=True):
    """Convert LCH colors to RGB

    Parameters
    ----------
    L: float
        Lightness
    C: float
        Chroma
    H: float
        Hue, angular, units defined by h_degrees parameter
    simplified: boolean
        Use simplified RGB with gamma 2.2 (default, True)
        or the conditional linear adjustment for sRGB (False)
    h_degrees: boolean
        Hue expected in degrees (default, True)
        or radians in domain [-pi to pi] (False)

    Returns
    -------
    r, g, b tuple (Red, Green and Blue)
    """
    if h_degrees:
        a = C * math.cos(math.radians(H))
        b = C * math.sin(math.radians(H))
    else:
        a = C * math.cos(H)
        b = C * math.sin(H)

    delta = 0.13793103448275862   # 6/29

    tx = ((L + 16) / 116.0) + (a / 500.0)
    if tx > delta:
        x = tx ** 3
    else:
        x = 3 * delta * delta * (tx - (4 / 29.0))

    ty = (L + 16) / 116.0
    if ty > delta:
        y = ty ** 3
    else:
        y = 3 * delta * delta * (ty - (4 / 29.0))

    tz = ((L + 16) / 116.0) - (b / 200.0)
    if tz > delta:
        z = tz ** 3
    else:
        z = 3 * delta * delta * (tz - (4 / 29.0))

    # uses reference white d65
    x = x * 0.95047
    z = z * 1.08883

    # XYZ to sRGB
    # expanded matrix multiplication
    rlin = (x * 3.2406) + (y * -1.5372) + (z * -0.4986)
    glin = (x * -0.9689) + (y * 1.8758) + (z * 0.0415)
    blin = (x * 0.0557) + (y * -0.2040) + (z * 1.0570)

    # includes gamma exponentiation
    if simplified:
        # Use simplified sRGB with gamma = 2.2
        r = rlin ** (1 / 2.2)
        g = glin ** (1 / 2.2)
        b = blin ** (1 / 2.2)
    else:
        # Use conditional
        if rlin <= 0.0031308:
            r = 12.92 * rlin
        else:
            r = (((1 + 0.055) * rlin) ** (1 / 2.4)) - 0.055

        if glin <= 0.0031308:
            g = 12.92 * glin
        else:
            g = (((1 + 0.055) * glin) ** (1 / 2.4)) - 0.055

        if blin <= 0.0031308:
            b = 12.92 * blin
        else:
            b = (((1 + 0.055) * blin) ** (1 / 2.4)) - 0.055

    return r, g, b


if __name__ == "__main__":
    import time
    r, g, b = np.random.random(3)
    print(r, g, b)
    while True:
        l, c, h = rgb_to_lch(r, g, b)
        print("                               ", l, c, h)
        r, g, b = lch_to_rgb(l, c, h)
        print(r, g, b)
        time.sleep(1)
