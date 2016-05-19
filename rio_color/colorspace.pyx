# cython: boundscheck=False
# cython: cdivision=True
# cython: wraparound=False
from __future__ import division
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

# Colorspace consts
# allows cdef funcs to access values w/o python calls
# needs to stay in sync with enum above
cdef enum:
    RGB = 0
    XYZ = 1
    LAB = 2
    LCH = 3


cpdef convert(double one, double two, double three, src, dst):
    cdef color color
    cdef int src_cs, dst_cs

    color = _convert(one, two, three, src, dst)
    return color.one, color.two, color.three


cpdef np.ndarray[FLOAT_t, ndim=3] convert_arr(np.ndarray[FLOAT_t, ndim=3] arr, src, dst):
    cdef double one, two, three
    cdef color color
    cdef size_t i, j
    cdef int src_cs, dst_cs

    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty_like(arr)

    for i in range(arr.shape[1]):
        for j in range(arr.shape[2]):
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
    cdef size_t i, j
    cdef color c_lch
    cdef color c_rgb

    if arr.shape[0] != 3:
        raise ValueError("The 0th dimension must contain 3 bands")

    cdef np.ndarray[FLOAT_t, ndim=3] out = np.empty_like(arr)

    for i in range(arr.shape[1]):
        for j in range(arr.shape[2]):
            r = arr[0, i, j]
            g = arr[1, i, j]
            b = arr[2, i, j]

            c_lch = _rgb_to_lch(r, g, b)
            c_lch.two *= satmult
            c_rgb = _lch_to_rgb(c_lch.one, c_lch.two, c_lch.three)

            out[0, i, j] = c_rgb.one
            out[1, i, j] = c_rgb.two
            out[2, i, j] = c_rgb.three

    return out


cdef color _convert(double one, double two, double three, int src, int dst):
    # TODO currently, every combination of COLORSPACES
    # must return a valid color. If this list grows,
    # things get ugly fast
    if src == RGB:
        if dst == LAB:
            return _rgb_to_lab(one, two, three)
        elif dst == LCH:
            return _rgb_to_lch(one, two, three)
        elif dst == XYZ:
            return _rgb_to_xyz(one, two, three)
    elif src == XYZ:
        if dst == LAB:
            return _xyz_to_lab(one, two, three)
        elif dst == LCH:
            return _xyz_to_lch(one, two, three)
        elif dst == RGB:
            return _xyz_to_rgb(one, two, three)
    elif src == LAB:
        if dst == XYZ:
            return _lab_to_xyz(one, two, three)
        elif dst == LCH:
            return _lab_to_lch(one, two, three)
        elif dst == RGB:
            return _lab_to_rgb(one, two, three)
    elif src == LCH:
        if dst == LAB:
            return _lch_to_lab(one, two, three)
        elif dst == XYZ:
            return _lch_to_xyz(one, two, three)
        elif dst == RGB:
           return _lch_to_rgb(one, two, three)


# Constants
cdef double bintercept = 4.0 / 29  # 0.137931
cdef double delta = 6.0 / 29  # 0.206896
cdef double t0 = delta ** 3  # 0.008856
cdef double alpha = (delta ** -2) / 3  # 7.787037


# Conversions composed of multiple steps

cdef color _rgb_to_lch(double r, double g, double b):
    cdef color color
    color = _rgb_to_xyz(r, g, b)
    color = _xyz_to_lab(color.one, color.two, color.three)
    color = _lab_to_lch(color.one, color.two, color.three)
    return color


cdef color _lch_to_rgb(double L, double C, double H):
    cdef color color
    color = _lch_to_lab(L, C, H)
    color = _lab_to_xyz(color.one, color.two, color.three)
    color = _xyz_to_rgb(color.one, color.two, color.three)
    return color


cdef color _lch_to_xyz(double L, double C, double H):
    cdef color color
    color = _lch_to_lab(L, C, H)
    color = _lab_to_xyz(color.one, color.two, color.three)
    return color


cdef color _xyz_to_lch(double x, double y, double z):
    cdef color color
    color = _xyz_to_lab(x, y, z)
    color = _lab_to_lch(color.one, color.two, color.three)
    return color


cdef color _rgb_to_lab(double r, double g, double b):
    cdef color color
    color = _rgb_to_xyz(r, g, b)
    color = _xyz_to_lab(color.one, color.two, color.three)
    return color


cdef color _lab_to_rgb(double L, double a, double b):
    cdef color color
    color = _lab_to_xyz(L, a, b)
    color = _xyz_to_rgb(color.one, color.two, color.three)
    return color


# Direct conversions

cdef color _rgb_to_xyz(double r, double g, double b):
    cdef double rl, gl, bl
    cdef color color

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

    color.one = x
    color.two = y
    color.three = z
    return color


cdef color _xyz_to_lab(double x, double y, double z):
    cdef double fx, fy, fz
    cdef double L, a, b
    cdef color color

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

    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    color.one = L
    color.two = a
    color.three = b
    return color

cdef color _lab_to_lch(double L, double a, double b):
    cdef color color

    color.one = L
    color.two = ((a * a) + (b * b)) ** 0.5
    color.three = atan2(b, a)
    return color


cdef color _lch_to_lab(double L, double C, double H):
    cdef double a, b
    cdef color color

    a = C * cos(H)
    b = C * sin(H)

    color.one = L
    color.two = a
    color.three = b
    return color


cdef color _lab_to_xyz(double L, double a, double b):
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


cdef color _xyz_to_rgb(double x, double y, double z):
    cdef double rlin, glin, blin
    cdef color color

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
    color.one = rlin ** (1 / 2.2)
    color.two = glin ** (1 / 2.2)
    color.three = blin ** (1 / 2.2)

    return color
