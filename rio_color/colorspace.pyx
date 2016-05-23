# cython: language_level=3, boundscheck=False, wraparound=False, nonecheck=False, cdivision=True, initializedcheck=False
from enum import IntEnum

import numpy as np

cimport numpy as np
from libc.math cimport cos, sin, atan2
cimport cython
ctypedef np.float64_t FLOAT_t


# See http://stackoverflow.com/a/4523537/519385
# for reasons why a fixed-length array should
# not be typedef'd without a wrapping struct
cdef struct st_color:
    double one
    double two
    double three

ctypedef st_color color


class ColorSpace(IntEnum):
    rgb = 0
    xyz = 1
    lab = 2
    lch = 3
    luv = 4

# Colorspace consts
# allows cdef funcs to access values w/o python calls
# needs to stay in sync with enum above
cdef enum:
    RGB = 0
    XYZ = 1
    LAB = 2
    LCH = 3
    LUV = 4


cpdef convert(double one, double two, double three, src, dst):
    cdef color color

    if src not in ColorSpace or dst not in ColorSpace:
        raise ValueError("Invalid colorspace")

    color = _convert(one, two, three, int(src), int(dst))
    return color.one, color.two, color.three


cpdef np.ndarray[FLOAT_t, ndim=3] convert_arr(np.ndarray[FLOAT_t, ndim=3] arr, src, dst):
    cdef double one, two, three
    cdef color color

    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    if src not in ColorSpace or dst not in ColorSpace:
        raise ValueError("Invalid colorspace")

    I = arr.shape[1]
    J = arr.shape[2]

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty(shape=(3, I, J))   # _like(arr)

    for i in range(I):
        for j in range(J):
            one = arr[0, i, j]
            two = arr[1, i, j]
            three = arr[2, i, j]
            color = _convert(one, two, three, src, dst)
            out[0, i, j] = color.one
            out[1, i, j] = color.two
            out[2, i, j] = color.three

    return out


cpdef np.ndarray[FLOAT_t, ndim=3] saturate_rgb(np.ndarray[FLOAT_t, ndim=3] arr, double satmult):
    """Convert array of RGB -> LCH, adjust saturation, back to RGB
    A special case of convert_arr with hardcoded color spaces and
    a bit of data manipulation inside the loop.
    """
    cdef double r, g, b
    cdef color c_lch
    cdef color c_rgb

    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    I = arr.shape[1]
    J = arr.shape[2]

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty(shape=(3, I, J))

    for i in range(I):
        for j in range(J):
            r = arr[0, i, j]
            g = arr[1, i, j]
            b = arr[2, i, j]

            c_lch = _convert(r, g, b, RGB, LCH)
            c_lch.two *= satmult
            c_rgb = _convert(c_lch.one, c_lch.two, c_lch.three, LCH, RGB)

            out[0, i, j] = c_rgb.one
            out[1, i, j] = c_rgb.two
            out[2, i, j] = c_rgb.three

    return out


cdef inline color _convert(double one, double two, double three, int src, int dst):
    cdef color c

    if src == RGB:

        if dst == LAB:
            c = _rgb_to_xyz(one, two, three)
            c = _xyz_to_lab(c.one, c.two, c.three)

        elif dst == LCH:
            c = _rgb_to_xyz(one, two, three)
            c = _xyz_to_lab(c.one, c.two, c.three)
            c = _lab_to_lch(c.one, c.two, c.three)

        elif dst == XYZ:
            c = _rgb_to_xyz(one, two, three)

        elif dst == LUV:
            c = _rgb_to_xyz(one, two, three)
            c = _xyz_to_luv(c.one, c.two, c.three)

    elif src == XYZ:

        if dst == LAB:
            c = _xyz_to_lab(one, two, three)

        elif dst == LCH:
            c = _xyz_to_lab(one, two, three)
            c = _lab_to_lch(c.one, c.two, c.three)

        elif dst == RGB:
            c = _xyz_to_rgb(one, two, three)

        elif dst == LUV:
            c = _xyz_to_luv(one, two, three)

    elif src == LAB:

        if dst == XYZ:
            c = _lab_to_xyz(one, two, three)

        elif dst == LCH:
            c = _lab_to_lch(one, two, three)

        elif dst == RGB:
            c = _lab_to_xyz(one, two, three)
            c = _xyz_to_rgb(c.one, c.two, c.three)

        elif dst == LUV:
            c = _lab_to_xyz(one, two, three)
            c = _xyz_to_luv(c.one, c.two, c.three)

    elif src == LCH:

        if dst == LAB:
            c = _lch_to_lab(one, two, three)

        elif dst == XYZ:
            c = _lch_to_lab(one, two, three)
            c = _lab_to_xyz(c.one, c.two, c.three)

        elif dst == RGB:
            c = _lch_to_lab(one, two, three)
            c = _lab_to_xyz(c.one, c.two, c.three)
            c = _xyz_to_rgb(c.one, c.two, c.three)

        elif dst == LUV:
            c = _lch_to_lab(one, two, three)
            c = _lab_to_xyz(c.one, c.two, c.three)
            c = _xyz_to_luv(c.one, c.two, c.three)

    elif src == LUV:

        if dst == LAB:
            c = _luv_to_xyz(one, two, three)
            c = _xyz_to_lab(c.one, c.two, c.three)

        elif dst == XYZ:
            c = _luv_to_xyz(one, two, three)

        elif dst == RGB:
            c = _luv_to_xyz(one, two, three)
            c = _xyz_to_rgb(c.one, c.two, c.three)

        elif dst == LCH:
            c = _luv_to_xyz(one, two, three)
            c = _xyz_to_lab(c.one, c.two, c.three)
            c = _lab_to_lch(c.one, c.two, c.three)

    elif src == dst:
        c.one = one
        c.two = two
        c.three = three

    return c


# Constants
DEF bintercept = 4.0 / 29  # 0.137931
DEF delta = 6.0 / 29  # 0.206896
DEF t0 = delta ** 3  # 0.008856
DEF alpha = (delta ** -2) / 3  # 7.787037
DEF third = 1.0 / 3
DEF uprime_n = 0.2009
DEF vprime_n = 0.4610
DEF kappa = (29.0 / 3) ** 3  # 903.3
DEF gamma = 2.2

# Compile time option to use
# simplified sRGB (True) or sRGB companding (False)
# SIMPLE=False is slightly slower but is more accurate at
# the extreme ends of scale - unit tests would need updating
DEF SIMPLE = True


# Direct colorspace conversions

cdef inline color _rgb_to_xyz(double r, double g, double b):
    cdef double rl, gl, bl
    cdef color color

    # convert RGB to linear scale

    IF SIMPLE:
        # Use "simplified sRGB"
        rl = r ** gamma
        gl = g ** gamma
        bl = b ** gamma
    ELSE:
        if r <= 0.04045:
            rl = r / 12.92
        else:
            rl = ((r + 0.055) / 1.055) ** 2.4
        if g <= 0.04045:
            gl = g / 12.92
        else:
            gl = ((g + 0.055) / 1.055) ** 2.4
        if b <= 0.04045:
            bl = b / 12.92
        else:
            bl = ((b + 0.055) / 1.055) ** 2.4

    # matrix mult for srgb->xyz,
    # includes adjustment for d65 reference white
    x = ((rl * 0.4124) + (gl * 0.3576) + (bl * 0.1805)) / 0.95047
    y = ((rl * 0.2126) + (gl * 0.7152) + (bl * 0.0722))
    z = ((rl * 0.0193) + (gl * 0.1192) + (bl * 0.9505)) / 1.08883

    color.one = x
    color.two = y
    color.three = z
    return color


cdef inline color _xyz_to_lab(double x, double y, double z):
    cdef double fx, fy, fz
    cdef double L, a, b
    cdef color color

    # convert XYZ to LAB colorspace
    if x > t0:
        fx = x ** third
    else:
        fx = (alpha * x) + bintercept

    if y > t0:
        fy = y ** third
    else:
        fy = (alpha * y) + bintercept

    if z > t0:
        fz = z ** third
    else:
        fz = (alpha * z) + bintercept

    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    color.one = L
    color.two = a
    color.three = b
    return color

cdef inline color _lab_to_lch(double L, double a, double b):
    cdef color color

    color.one = L
    color.two = ((a * a) + (b * b)) ** 0.5
    color.three = atan2(b, a)
    return color


cdef inline color _lch_to_lab(double L, double C, double H):
    cdef double a, b
    cdef color color

    a = C * cos(H)
    b = C * sin(H)

    color.one = L
    color.two = a
    color.three = b
    return color


cdef inline color _lab_to_xyz(double L, double a, double b):
    cdef double x, y, z
    cdef color color

    tx = ((L + 16) / 116.0) + (a / 500.0)
    if tx > delta:
        x = tx ** 3
    else:
        x = 3 * delta * delta * (tx - bintercept)

    ty = (L + 16) / 116.0
    if ty > delta:
        y = ty ** 3
    else:
        y = 3 * delta * delta * (ty - bintercept)

    tz = ((L + 16) / 116.0) - (b / 200.0)
    if tz > delta:
        z = tz ** 3
    else:
        z = 3 * delta * delta * (tz - bintercept)

    color.one = x
    color.two = y
    color.three = z
    return color


cdef inline color _xyz_to_rgb(double x, double y, double z):
    cdef double rlin, glin, blin, r, g, b
    cdef color color

    # uses reference white d65
    x = x * 0.95047
    z = z * 1.08883

    # XYZ to sRGB
    # expanded matrix multiplication
    rlin = (x * 3.2406) + (y * -1.5372) + (z * -0.4986)
    glin = (x * -0.9689) + (y * 1.8758) + (z * 0.0415)
    blin = (x * 0.0557) + (y * -0.2040) + (z * 1.0570)

    IF SIMPLE:
        # constrain to 0..1 to deal with any float drift
        if rlin > 1.0:
            rlin = 1.0
        elif rlin < 0.0:
            rlin = 0.0
        if glin > 1.0:
            glin = 1.0
        elif glin < 0.0:
            glin = 0.0
        if blin > 1.0:
            blin = 1.0
        elif blin < 0.0:
            blin = 0.0

        # Use simplified sRGB
        r = rlin ** (1 / gamma)
        g = glin ** (1 / gamma)
        b = blin ** (1 / gamma)
    ELSE:
        if rlin <= 0.0031308:
            r = 12.92 * rlin
        else:
            r = (1.055 * (rlin ** (1 / 2.4))) - 0.055
        if glin <= 0.0031308:
            g = 12.92 * glin
        else:
            g = (1.055 * (glin ** (1 / 2.4))) - 0.055
        if blin <= 0.0031308:
            b = 12.92 * blin
        else:
            b = (1.055 * (blin ** (1 / 2.4))) - 0.055

    color.one = r
    color.two = g
    color.three = b

    return color


cdef inline color _xyz_to_luv(double x, double y, double z):
    cdef color color
    cdef double L, u, v, uprime, vprime, denom

    denom = x + (15 * y) + (3 * z)
    uprime = (4 * x) / denom
    vprime = (9 * y) / denom

    if y <= t0:
        L = kappa * y
    else:
        L = (116 * (y ** third)) - 16

    u = 13 * L * (uprime - uprime_n)
    v = 13 * L * (vprime - vprime_n)

    color.one = L
    color.two = u
    color.three = v
    return color


cdef inline color _luv_to_xyz(double L, double u, double v):
    cdef color color
    cdef double x, y, z, uprime, vprime

    uprime = (u / (13 * L)) + uprime_n
    vprime = (v / (13 * L)) + vprime_n

    if L <= 8.0:
        y = L * ((3.0 / 29) ** 3)
    else:
        y = ((L + 16) / 116.0) ** 3

    x = y * ((9 * uprime) / (4 * vprime))
    z = y * ((12 - (3 * uprime) - (20 * vprime)) / (4 * vprime))

    color.one = x
    color.two = y
    color.three = z
    return color
