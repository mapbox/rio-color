import pytest
import numpy as np

from rio_color.utils import to_math_type
from rio_color.operations import (
    sigmoidal,
    gamma,
    saturation,
    simple_atmo,
    parse_operations,
    simple_atmo_opstring,
)


@pytest.fixture
def arr():

    return to_math_type(
        np.array(
            [
                # red
                [[1, 2], [3, 4]],
                # green
                [[5, 6], [7, 8]],
                # blue
                [[9, 10], [11, 12]],
            ]
        ).astype("uint8")
        * 10
    )


@pytest.fixture
def arr_rgba():
    return to_math_type(
        np.array(
            [
                [[1, 2], [3, 4]],  # red
                [[5, 6], [7, 8]],  # green
                [[9, 10], [11, 12]],  # blue
                [[0, 0], [25.5, 25.5]],  # alpha
            ]
        ).astype("uint8")
        * 10
    )


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
    # test output contains NaN
    with pytest.raises(ValueError):
        x = gamma(arr, np.nan)
    with pytest.raises(ValueError):
        x = gamma(arr * -1, 2.2)


def test_sat(arr):
    x = saturation(arr, 50)
    assert x[0][0][0] - 0.15860622 < 1e-4


def test_sat_rgba_direct(arr_rgba):
    # Anything but 3-band RGB will fail
    with pytest.raises(ValueError):
        saturation(arr_rgba, 50)
    with pytest.raises(ValueError):
        saturation(arr_rgba[0:2], 50)


def test_atmo(arr):
    x = simple_atmo(arr, 0.03, 10, 0.15)
    assert x[0][0][0] - 0.080560341 < 1e-4

    # Gamma output is not within the range 0..1
    with pytest.raises(ValueError):
        x = simple_atmo(arr, 2.0, 10, 0.15)

    # Sigmoidal contrast output contains NaN
    with pytest.raises(ValueError):
        x = simple_atmo(arr, 0.03, 1000, -0.15)


def test_parse_gamma(arr):
    f = parse_operations("gamma rgb 0.95")[0]
    assert np.array_equal(f(arr), gamma(arr, 0.95))


def test_parse_sigmoidal(arr):
    f = parse_operations("sigmoidal rgb 5 0.53")[0]
    assert np.array_equal(f(arr), sigmoidal(arr, contrast=5, bias=0.53))


def test_parse_multi(arr):
    f1, f2 = parse_operations("gamma rgb 0.95 sigmoidal rgb 35 0.13")
    assert np.array_equal(
        f2(f1(arr)), sigmoidal(gamma(arr, g=0.95), contrast=35, bias=0.13)
    )


def test_parse_comma(arr):
    # Commas are optional whitespace, treated like empty string
    f1, f2 = parse_operations("gamma r,g,b 0.95, sigmoidal r,g,b 35 0.13")
    assert np.array_equal(
        f2(f1(arr)), sigmoidal(gamma(arr, g=0.95), contrast=35, bias=0.13)
    )


def test_parse_saturation_rgb(arr):
    f = parse_operations("saturation 1.25")[0]
    assert np.allclose(f(arr), saturation(arr, 1.25))


def test_parse_rgba(arr, arr_rgba):
    f = parse_operations("gamma rg 0.95")[0]
    rgb = f(arr)
    assert rgb.shape[0] == 3

    rgba = f(arr_rgba)
    assert rgba.shape[0] == 4
    # rgb bands are same
    assert np.allclose(rgba[0:3], rgb[0:3])
    # alpha unaltered
    assert np.array_equal(rgba[3], arr_rgba[3])


def test_saturation_rgba(arr, arr_rgba):
    f = parse_operations("saturation 1.25")[0]

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
        parse_operations("foob 123")


def test_parse_bands(arr):
    fa = parse_operations("gamma 1,2 0.95")[0]
    fb = parse_operations("gamma Rg 0.95")[0]
    assert np.array_equal(fa(arr), fb(arr))

    with pytest.raises(ValueError):
        parse_operations("gamma 7,8,9 1.05")


def test_parse_multi_saturation_first(arr):
    f1, f2 = parse_operations("saturation 1.25 gamma rgb 0.95")
    assert np.array_equal(f2(f1(arr)), gamma(saturation(arr, 1.25), g=0.95))


def test_parse_multi_name(arr):
    f1, f2 = parse_operations("saturation 1.25 gamma rgb 0.95")
    assert f1.__name__ == "saturation"
    assert f2.__name__ == "gamma"


def test_simple_atmos_opstring(arr):
    x = simple_atmo(arr, 0.03, 10, 0.15)
    ops = simple_atmo_opstring(0.03, 10, 0.15)
    for op in parse_operations(ops):
        arr = op(arr)
    assert np.allclose(x, arr)
