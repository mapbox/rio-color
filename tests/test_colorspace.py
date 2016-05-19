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


def test_bad_colorspace():
    with pytest.raises(TypeError) as exc:
        convert(0.1, 0.1, 0.1, src='FOO', dst='RGB')

    with pytest.raises(AttributeError) as exc:
        convert(0.1, 0.1, 0.1, src=cs.foo, dst=cs.bar)


def _assert_iter_floateq(a, b, tol):
    for x, y in zip(a, b):
        assert abs(x - y) < tol


def test_convert_roundtrips():
    # start with RGB
    rgb = (0.392156, 0.776470, 0.164705)

    # all other colorspaces
    cspaces = tuple(x for x in dict(cs.__members__).values() if x != cs.rgb)

    for cspace in cspaces:
        other = convert(*rgb, src=cs.rgb, dst=cspace)
        back = convert(*other, src=cspace, dst=cs.rgb)
        _assert_iter_floateq(back, rgb, tol=1e-4)
