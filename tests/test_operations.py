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


def test_gamma(arr):
    x = gamma(arr, 0.95)
    assert x[0][0][0] - 0.033069782 < 1e-4


def test_sat(arr):
    x = saturation(arr, 50)
    assert x[0][0][0] - 0.1513809257 < 1e-4


def test_atmo(arr):
    x = simple_atmo(arr, 0.03, 10, 15)
    assert x[0][0][0] - 0.080560341 < 1e-4


def test_parse_one(arr):
    f = list(parse_operations(["gamma 1,2,3 0.95", ]))[0]
    assert np.array_equal(f(arr), gamma(arr, 0.95))


def test_parse_multi(arr):
    f1, f2 = list(parse_operations([
        "gamma 1,2,3 0.95", "sigmoidal 1,2,3 35 0.13"]))
    assert np.array_equal(
        f2(f1(arr)),
        sigmoidal(gamma(arr, g=0.95), contrast=35, bias=0.13))

def test_parse_rgb(arr):
    f = list(parse_operations(["saturation 125", ]))[0]
    assert np.array_equal(f(arr), saturation(arr, 125))


def test_parse_bad_op():
    with pytest.raises(ValueError):
        list(parse_operations(["foob 123"]))


def test_parse_bands(arr):
    fa = list(parse_operations(["gamma 1,2 0.95", ]))[0]
    fb = list(parse_operations(["gamma R,g 0.95", ]))[0]
    assert np.array_equal(fa(arr), fb(arr))

    with pytest.raises(ValueError):
        list(parse_operations(["gamma 7,8,9 1.05"]))
