import itertools

import numpy as np
import pytest

# public 3d array funcs
from rio_color.colorspace import convert_arr, saturate_rgb

# public scalar func
from rio_color.colorspace import convert

# enums required to define src and dst for convert and convert_arr
from rio_color.colorspace import ColorSpace as cs


tests = (
    # (rgb, expected_lch)
    ((0, 0, 0), (0, 0, 0)),
    ((1.0, 0, 0), (53.2, 104.6, 0.7)),
    ((0.392156, 0.776470, 0.164705), (72.1, 85.2, 2.3)),
    # using srgb companding, it becomes (71.7, 83.5, 2.3))
    ((1.0, 1.0, 1.0), (100, 0, -1.1)),
)

test_tol = 1

def _make_array(x, y, z, dtype='float64'):
    """ make a 3, 1, 1 array
    """
    return np.array([
        [[x]],
        [[y]],
        [[z]]]).astype(dtype)

def test_rgb2lch():
    for rgb, ex_lch in tests:
        assert ex_lch == tuple(round(x, test_tol)
                               for x in convert(*rgb, src=cs.rgb, dst=cs.lch))


def test_roundtrip():
    for rgb, _ in tests:
        assert tuple(round(x, test_tol) for x in rgb) == \
            tuple(round(x, test_tol) for x in convert(
                *convert(*rgb, src=cs.rgb, dst=cs.lch), src=cs.lch, dst=cs.rgb))


def test_lch2rgb():
    for ex_rgb, lch in tests:
        assert tuple(round(x, test_tol) for x in ex_rgb) == \
            tuple(round(x, test_tol)
                  for x in convert(*lch, src=cs.lch, dst=cs.rgb))


def test_arr_rgb():
    for rgb, ex_lch in tests:
        rgb = _make_array(*rgb)
        ex_lch = _make_array(*ex_lch)
        assert np.allclose(
            convert_arr(rgb, cs.rgb, cs.lch), ex_lch, atol=(test_tol / 10.0))


def test_arr_lch():
    for rgb, lch in tests:
        rgb = _make_array(*rgb)
        lch = _make_array(*lch)
        assert np.allclose(
            convert_arr(lch, cs.lch, cs.rgb), rgb, atol=(test_tol / 10.0))


def test_saturation_1():
    for rgb, _ in tests:
        rgb = _make_array(*rgb)
        assert np.allclose(
            saturate_rgb(rgb, 1.0), rgb, atol=(test_tol / 10.0))


def test_saturation_bw():
    rgb = _make_array(0.392156, 0.776470, 0.164705)
    sat = saturate_rgb(rgb, 0.0)
    assert round(sat[0, 0, 0], test_tol) == \
        round(sat[1, 0, 0], test_tol) == \
        round(sat[2, 0, 0], test_tol)


def test_saturation():
    rgb = _make_array(0.392156, 0.776470, 0.164705)
    saturated = _make_array(0.3425, 0.78372, 0.0)
    assert np.allclose(
        saturate_rgb(rgb, 1.1),
        saturated,
        atol=(test_tol / 10.0))


def test_bad_array_bands():
    bad = np.random.random((2, 3, 3))
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert '3 bands' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert '3 bands' in str(exc.value)

def test_bad_array_dims():
    bad = np.random.random((3, 3))
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert 'wrong number of dimensions' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert 'wrong number of dimensions' in str(exc.value)


def test_bad_array_type():
    bad = np.random.random((3, 3, 3)).astype('uint8')
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert 'dtype mismatch' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, cs.rgb, cs.lch)
    assert 'dtype mismatch' in str(exc.value)


def test_array_bad_colorspace():
    arr = np.random.random((3, 3))
    with pytest.raises(ValueError) as exc:
        convert_arr(arr, src='FOO', dst='RGB')

    with pytest.raises(ValueError):
        convert_arr(arr, src=999, dst=999)


def test_bad_colorspace():
    with pytest.raises(ValueError) as exc:
        convert(0.1, 0.1, 0.1, src='FOO', dst='RGB')

    with pytest.raises(ValueError):
        convert(0.1, 0.1, 0.1, src=999, dst=999)

    with pytest.raises(AttributeError) as exc:
        convert(0.1, 0.1, 0.1, src=cs.foo, dst=cs.bar)


def _iter_floateq(a, b, tol):
    for x, y in zip(a, b):
        return abs(x - y) < tol


def test_convert_roundtrips():
    cspaces = tuple(x for x in dict(cs.__members__).values())
    # TODO relative tolerance and figure out how to decrease float drift
    tolerance = 0.01

    for rgb in itertools.combinations([0, 0.1, 0.3, 0.6, 0.9, 1.0], 3):
        colors = {}

        # RGB to other, roundtrip
        for cspace in cspaces:
            if cspace == cs.rgb:
                continue
            other = convert(*rgb, src=cs.rgb, dst=cspace)
            # Collect some valid colors
            colors[cspace] = other
            back = convert(*other, src=cspace, dst=cs.rgb)
            assert _iter_floateq(back, rgb, tol=tolerance)

        # other to other roundtrip, including self
        for src, color in colors.items():
            for dst in cspaces:
                other = convert(*color, src=src, dst=dst)
                back = convert(*other, src=dst, dst=src)
                assert _iter_floateq(back, color, tol=tolerance)
