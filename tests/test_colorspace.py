from itertools import product
import collections
import math

import numpy as np
import pytest

# public 3d array funcs
from rio_color.colorspace import convert_arr, saturate_rgb

# public scalar func
from rio_color.colorspace import convert

# enums required to define src and dst for convert and convert_arr
from rio_color.colorspace import ColorSpace as cs

from colormath.color_objects import LuvColor, sRGBColor, XYZColor, LCHabColor, LabColor

from colormath.color_conversions import convert_color

to_colormath = {
    cs.rgb: sRGBColor,
    cs.xyz: XYZColor,
    cs.lab: LabColor,
    cs.lch: LCHabColor,
    cs.luv: LuvColor,
}


tests = (
    # (rgb, expected_lch)
    ((0, 0, 0), (0, 0, 0)),
    ((1.0, 0, 0), (53.2, 104.6, 0.7)),
    ((0.392156, 0.776470, 0.164705), (71.7, 83.5, 2.3)),
    ((0.0392, 0.1960, 0.3529), (20.3517, 27.8757, -1.4612)),
    ((0.0456, 0.1929, 0.3941), (20.8945, 34.9429, -1.3244)),
    ((1.0, 1.0, 1.0), (100, 0, 2.8)),
)

test_tol = 1


@pytest.mark.parametrize("pair", tests)
def test_fixtures(pair):
    # use colormath to confirm test values
    rgb, lch = pair
    cmlch = convert_color(sRGBColor(*rgb), LCHabColor).get_value_tuple()

    assert _near(lch[0:2], cmlch[0:2], 0.2)

    if lch[0] < 99.999999:
        # If L == 100, the hue is indeterminate
        # Otherwise, normalize to [0, 2*pi] and compare
        h = lch[2] % (math.pi * 2)
        cmh = math.radians(cmlch[2]) % (math.pi * 2)
        assert _near([h], [cmh], 0.2)


def _near(a, b, tol):

    if not isinstance(tol, collections.Iterable):
        tol = [tol] * len(a)

    for x, y, t in zip(a, b, tol):
        if abs(x - y) > t:
            return False
    return True


def _make_array(x, y, z, dtype="float64"):
    """make a 3, 1, 1 array"""
    return np.array([[[x]], [[y]], [[z]]]).astype(dtype)


@pytest.mark.parametrize("pair", tests)
def test_rgb2lch(pair):
    rgb, lch = pair
    alch = convert(*rgb, src=cs.rgb, dst=cs.lch)
    assert alch[0] >= 0
    assert _near(alch, lch, (1.0, 1.0, 0.25))


@pytest.mark.parametrize("pair", tests)
def test_roundtrip(pair):
    rgb, lch = pair
    argb = convert(*convert(*rgb, src=cs.rgb, dst=cs.lch), src=cs.lch, dst=cs.rgb)
    for v in argb:
        assert v > -0.0001
        assert v < 1.0001
    assert _near(argb, rgb, 0.1)


@pytest.mark.parametrize("pair", tests)
def test_lch2rgb(pair):
    rgb, lch = pair
    argb = convert(*lch, src=cs.lch, dst=cs.rgb)
    assert _near(argb, rgb, (1.0, 1.0, 0.1))


@pytest.mark.parametrize("pair", tests)
def test_arr_rgb(pair):
    rgb, lch = pair
    rgb = _make_array(*rgb)
    lch = _make_array(*lch)
    assert np.allclose(convert_arr(rgb, cs.rgb, cs.lch), lch, atol=0.2)


@pytest.mark.parametrize("pair", tests)
def test_arr_lch(pair):
    rgb, lch = pair
    rgb = _make_array(*rgb)
    lch = _make_array(*lch)
    assert np.allclose(convert_arr(lch, cs.lch, cs.rgb), rgb, atol=0.2)


@pytest.mark.parametrize("pair", tests)
def test_saturation_1(pair):
    rgb, lch = pair
    rgb = _make_array(*rgb)
    assert np.allclose(saturate_rgb(rgb, 1.0), rgb, atol=0.2)


def test_saturation_bw():
    rgb = _make_array(0.392156, 0.776470, 0.164705)
    sat = saturate_rgb(rgb, 0.0)
    assert _near((sat[0, 0, 0],), (sat[1, 0, 0],), tol=0.1)
    assert _near((sat[1, 0, 0],), (sat[2, 0, 0],), tol=0.1)


def test_saturation():
    rgb = _make_array(0.392156, 0.776470, 0.164705)
    saturated = _make_array(0.3425, 0.78372, 0.0)
    assert np.allclose(saturate_rgb(rgb, 1.1), saturated, atol=0.2)

    rgb = _make_array(0.0392, 0.1960, 0.3529)
    saturated = _make_array(0.0456, 0.1929, 0.3941)
    assert np.allclose(saturate_rgb(rgb, 1.25), saturated, atol=0.2)


def test_bad_array_bands():
    bad = np.random.random((2, 3, 3))
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert "3 bands" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert "3 bands" in str(exc.value)


def test_bad_array_dims():
    bad = np.random.random((3, 3))
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert "wrong number of dimensions" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert "wrong number of dimensions" in str(exc.value)


def test_bad_array_type():
    bad = np.random.random((3, 3, 3)).astype("uint8")
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert "dtype mismatch" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert "dtype mismatch" in str(exc.value)


def test_array_bad_colorspace():
    arr = np.random.random((3, 3))
    with pytest.raises(ValueError):
        convert_arr(arr, src="FOO", dst="RGB")

    with pytest.raises(ValueError):
        convert_arr(arr, src=999, dst=999)


def test_bad_colorspace_string():
    """String colorspaces raise ValueError"""
    with pytest.raises(ValueError):
        convert(0.1, 0.1, 0.1, src="FOO", dst="RGB")


def test_bad_colorspace_invalid_int():
    """Invalid colorspace integers raise ValueError"""
    with pytest.raises(ValueError):
        convert(0.1, 0.1, 0.1, src=999, dst=999)


def test_bad_colorspace_invalid_enum():
    """Invalid colorspace enum names raise AttributeError"""
    with pytest.raises(AttributeError):
        convert(0.1, 0.1, 0.1, src=cs.foo, dst=cs.bar)


def assert_color_roundtrip(color, src, dst, tolerance):
    """Asserts roundtrip of color correction within a given tolerance

    Helper function for tests below.
    """
    other = convert(*color, src=src, dst=dst)
    rio_roundtrip = convert(*other, src=dst, dst=src)

    if _near(rio_roundtrip, color, tol=tolerance):
        return True
    else:
        # Did not roundtrip properly, can colormath do it?
        src_cm = to_colormath[src]
        dst_cm = to_colormath[dst]

        cm_roundtrip = convert_color(
            convert_color(src_cm(*color), dst_cm, illuminant="d65"),
            src_cm,
            illuminant="d65",
        ).get_value_tuple()

        assert _near(rio_roundtrip, cm_roundtrip, tol=tolerance)


rgb_vals = [0.0, 0.01, 0.3, 0.5, 0.7, 0.99, 1.0]
rgb_colors = xyz_colors = list(product(rgb_vals, repeat=3))

# In parameterizing destination colorspaces we use a list comprehension,
# omitting the source colorspace.
# Test roundtrip from RGB to everything else


@pytest.mark.parametrize("color", rgb_colors)
@pytest.mark.parametrize("dst", [v for v in cs if v not in (cs.rgb,)])
@pytest.mark.parametrize("tolerance", [0.1])
def test_rgb_convert_roundtrip(color, dst, tolerance):
    assert_color_roundtrip(color, cs.rgb, dst, tolerance)
