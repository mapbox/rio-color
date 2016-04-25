import pytest
import numpy as np

from rio_color.utils import to_math_type
from rio_color.operations import (
    sigmoidal, gamma, saturation,
    rgb2lch, lch2rgb, simple_atmo, parse_operations)


@pytest.fixture
def arr():

    return to_math_type(np.array([
        # red
        [[1, 2],
         [3, 4]],

        # green
        [[5, 6],
         [7, 8]],

        # blue
        [[9, 10],
         [11, 12]]
    ]).astype('uint8') * 10)


@pytest.fixture
def arr_rgba():
    return to_math_type(np.array([
        [[1, 2], [3, 4]],  # red
        [[5, 6], [7, 8]],  # green
        [[9, 10], [11, 12]],  # blue
        [[0, 0], [25.5, 25.5]]  # alpha
    ]).astype('uint8') * 10)


def test_sigmoidal(arr):
    x = sigmoidal(arr, 10, 0.15)
    assert x[0][0][0] - 0.08056034 < 1e-4

    # contrast < 0
    x = sigmoidal(arr, -10, 0.15)
    assert x[0][0][0] - 0.020186627 < 1e-4

    # bias zero, make it a tiny epsilon
    x = sigmoidal(arr, 10, 0)
    assert x[0][0][0] - 0.19362122 < 1e-4

    # contrast zzero, arrays are equal
    x = sigmoidal(arr, 0, 0.15)
    assert np.array_equal(x, arr)

    # output contains NaN
    with pytest.raises(ValueError):
        x = sigmoidal(arr, 100, -0.5)

    # output is not within the range of 0..1
    with pytest.raises(ValueError):
        arr[0][0][0] = 1.0
        arr[0][0][1] = 2.0
        x = sigmoidal(arr, 10, -0.5)


def test_gamma(arr):
    x = gamma(arr, 0.95)
    assert x[0][0][0] - 0.033069782 < 1e-4
    # output is not within the range of 0..1
    with pytest.raises(ValueError):
        x = gamma(arr, -2.0)
    # test output contains inf and is out of range 0..1
    with pytest.raises(ValueError):
        x = gamma(arr, -0.001)


def test_sat(arr):
    x = saturation(arr, 50)
    assert x[0][0][0] - 0.1513809257 < 1e-4


def test_sat_rgba_direct(arr_rgba):
    # Anything but 3-band RGB will fail
    with pytest.raises(ValueError):
        saturation(arr_rgba, 50)
    with pytest.raises(ValueError):
        saturation(arr_rgba[0:2], 50)


def test_atmo(arr):
    x = simple_atmo(arr, 0.03, 10, 15)
    assert x[0][0][0] - 0.080560341 < 1e-4

    # Gamma output is not within the range 0..1
    with pytest.raises(ValueError):
        x = simple_atmo(arr, 2.0, 10, 15)

    # Sigmoidal contrast output contains NaN
    with pytest.raises(ValueError):
        x = simple_atmo(arr, 0.03, 1000, -5)


def test_parse_gamma(arr):
    f = list(parse_operations(["gamma 1,2,3 0.95", ]))[0]
    assert np.array_equal(f(arr), gamma(arr, 0.95))


def test_parse_sigmoidal(arr):
    f = list(parse_operations(["sigmoidal 1,2,3 5 0.53", ]))[0]
    assert np.array_equal(
        f(arr),
        sigmoidal(arr, contrast=5, bias=0.53))


def test_parse_multi(arr):
    f1, f2 = list(parse_operations([
        "gamma 1,2,3 0.95", "sigmoidal 1,2,3 35 0.13"]))
    assert np.array_equal(
        f2(f1(arr)),
        sigmoidal(gamma(arr, g=0.95), contrast=35, bias=0.13))


def test_parse_rgb(arr):
    f = list(parse_operations(["saturation 125", ]))[0]
    assert np.allclose(f(arr), saturation(arr, 125))


def test_parse_rgba(arr, arr_rgba):
    f = list(parse_operations(["gamma r,g 0.95", ]))[0]
    rgb = f(arr)
    assert rgb.shape[0] == 3

    rgba = f(arr_rgba)
    assert rgba.shape[0] == 4
    # rgb bands are same
    assert np.allclose(rgba[0:3], rgb[0:3])
    # alpha unaltered
    assert np.array_equal(rgba[3], arr_rgba[3])


def test_saturation_rgba(arr, arr_rgba):
    f = list(parse_operations(["saturation 125", ]))[0]

    satrgb = f(arr)
    assert satrgb.shape[0] == 3

    satrgba = f(arr_rgba)
    # Still rgba
    assert satrgba.shape[0] == 4
    # alpha is unaltered
    assert np.array_equal(satrgba[3], arr_rgba[3])
    # first 3 bands are same b/t rgb and rgba
    assert np.allclose(satrgba[0:3], satrgb[0:3])


def test_parse_bad_op():
    with pytest.raises(ValueError):
        list(parse_operations(["foob 123"]))


def test_parse_bands(arr):
    fa = list(parse_operations(["gamma 1,2 0.95", ]))[0]
    fb = list(parse_operations(["gamma R,g 0.95", ]))[0]
    assert np.array_equal(fa(arr), fb(arr))

    with pytest.raises(ValueError):
        list(parse_operations(["gamma 7,8,9 1.05"]))
