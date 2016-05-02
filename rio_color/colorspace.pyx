# cython: boundscheck=False
# cython: cdivision=True
# cython: wraparound=False
from __future__ import division

import numpy as np

cimport numpy as np
from libc.math cimport cos, sin, atan2
cimport cython
ctypedef np.float64_t FLOAT_t


cdef struct st_rgb:
    double r
    double g
    double b

ctypedef st_rgb rgb

cdef struct st_lch:
    double l
    double c
    double h

ctypedef st_lch lch


def rgb_to_lch(r, g, b):
    """Convert RGB colors to LCH

    Parameters
    ----------
    r: float
        0 to 1, Red
    g: float
        0 to 1, Blue
    b: float
        0 to 1, Blue

    Returns
    -------
    L, C, H tuple (Lightness, Chroma, Hue)
    H is in radians
    """
    cdef lch color
    color = _rgb_to_lch(r, g, b)
    return color.l, color.c, color.h


def lch_to_rgb(l, c, h):
    """Convert LCH colors to RGB

    Parameters
    ----------
    L: float
        Lightness
    C: float
        Chroma
    H: float
        Hue, radians

    Returns
    -------
    r, g, b tuple (Red, Green and Blue)
    scaled float 0..1
    """
    cdef rgb color
    color = _lch_to_rgb(l, c, h)
    return color.r, color.g, color.b


cpdef np.ndarray[FLOAT_t, ndim=3] saturate_rgb(np.ndarray[FLOAT_t, ndim=3] arr, double satmult):
    """Convert array of RGB -> LCH, adjust saturation, back to RGB
    """
    cdef double r, g, b
    cdef size_t i, j
    cdef lch c_lch
    cdef rgb c_rgb
    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty_like(arr)

    for i in range(arr.shape[1]):
        for j in range(arr.shape[2]):
            r = arr[0, i, j]
            g = arr[1, i, j]
            b = arr[2, i, j]

            c_lch = _rgb_to_lch(r, g, b)
            c_lch.c *= satmult
            c_rgb = _lch_to_rgb(c_lch.l, c_lch.c, c_lch.h)

            out[0, i, j] = c_rgb.r
            out[1, i, j] = c_rgb.g
            out[2, i, j] = c_rgb.b

    return out


cpdef np.ndarray[FLOAT_t, ndim=3] arr_rgb_to_lch(np.ndarray[FLOAT_t, ndim=3] arr):
    cdef double r, g, b
    cdef size_t i, j
    cdef lch color
    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty_like(arr)

    for i in range(arr.shape[1]):
        for j in range(arr.shape[2]):
            r = arr[0, i, j]
            g = arr[1, i, j]
            b = arr[2, i, j]
            color = _rgb_to_lch(r, g, b)
            out[0, i, j] = color.l
            out[1, i, j] = color.c
            out[2, i, j] = color.h

    return out


cpdef np.ndarray[FLOAT_t, ndim=3] arr_lch_to_rgb(np.ndarray[FLOAT_t, ndim=3] arr):
    cdef double l, c, h
    cdef size_t i, j
    cdef rgb color
    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty_like(arr)

    for i in range(arr.shape[1]):
        for j in range(arr.shape[2]):
            l = arr[0, i, j]
            c = arr[1, i, j]
            h = arr[2, i, j]
            color = _lch_to_rgb(l, c, h)
            out[0, i, j] = color.r
            out[1, i, j] = color.g
            out[2, i, j] = color.b

    return out

# Constants
cdef double bintercept = 4.0 / 29  # 0.137931
cdef double delta = 6.0 / 29  # 0.206896
cdef double t0 = delta ** 3  # 0.008856
cdef double alpha = (delta ** -2) / 3  # 7.787037


cdef lch _rgb_to_lch(double r, double g, double b):
    cdef lch color

    # convert RGB to linear scale
    # if simplified:
    # Use gamma = 2.2, "simplified sRGB"
    rl = r ** 2.2
    gl = g ** 2.2
    bl = b ** 2.2

    # matrix mult for srgb->xyz,
    # includes adjustment for d65 reference white
    x = ((rl * 0.4124) + (gl * 0.3576) + (bl * 0.1805)) / 0.95047
    y = ((rl * 0.2126) + (gl * 0.7152) + (bl * 0.0722))
    z = ((rl * 0.0193) + (gl * 0.1192) + (bl * 0.9505)) / 1.08883

    # convert XYZ to LAB colorspace
    if x > t0:
        fx = x ** 0.3333333333333333
    else:
        fx = (alpha * x) + bintercept

    if y > t0:
        fy = y ** 0.3333333333333333
    else:
        fy = (alpha * y) + bintercept

    if z > t0:
        fz = z ** 0.3333333333333333
    else:
        fz = (alpha * z) + bintercept

    color.l = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    color.c = ((a * a) + (b * b)) ** 0.5
    color.h = atan2(b, a)

    return color


cdef rgb _lch_to_rgb(double L, double C, double H):
    cdef double a, b
    cdef rgb color

    a = C * cos(H)
    b = C * sin(H)

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

    # uses reference white d65
    x = x * 0.95047
    z = z * 1.08883

    # XYZ to sRGB
    # expanded matrix multiplication
    rlin = (x * 3.2406) + (y * -1.5372) + (z * -0.4986)
    glin = (x * -0.9689) + (y * 1.8758) + (z * 0.0415)
    blin = (x * 0.0557) + (y * -0.2040) + (z * 1.0570)

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

    # includes gamma exponentiation
    # Use simplified sRGB with gamma = 2.2
    color.r = rlin ** (1 / 2.2)
    color.g = glin ** (1 / 2.2)
    color.b = blin ** (1 / 2.2)

    return color
