import numpy as np
import pytest

# public 3d array funcs
from rio_color.colorspace import convert_arr, saturate_rgb

# public single-arg wrappers
from rio_color.colorspace import convert


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
        assert ex_lch == tuple(round(x, test_tol) for x in convert(*rgb, src='RGB', dst='LCH'))


def test_roundtrip():
    for rgb, _ in tests:
        assert tuple(round(x, test_tol) for x in rgb) == \
            tuple(round(x, test_tol) for x in convert(
                *convert(*rgb, src='RGB', dst='LCH'), src='LCH', dst='RGB'))


def test_lch2rgb():
    for ex_rgb, lch in tests:
        assert tuple(round(x, test_tol) for x in ex_rgb) == \
            tuple(round(x, test_tol) for x in convert(*lch, src='LCH', dst='RGB'))


def test_arr_rgb():
    for rgb, ex_lch in tests:
        rgb = _make_array(*rgb)
        ex_lch = _make_array(*ex_lch)
        assert np.allclose(
            convert_arr(rgb, 'RGB', 'LCH'), ex_lch, atol=(test_tol / 10.0))


def test_arr_lch():
    for rgb, lch in tests:
        rgb = _make_array(*rgb)
        lch = _make_array(*lch)
        assert np.allclose(
            convert_arr(lch, 'LCH', 'RGB'), rgb, atol=(test_tol / 10.0))


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
        convert_arr(bad, 'RGB', 'LCH')
    assert '3 bands' in str(exc.value)

def test_bad_array_dims():
    bad = np.random.random((3, 3))
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert 'wrong number of dimensions' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, 'RGB', 'LCH')
    assert 'wrong number of dimensions' in str(exc.value)


def test_bad_array_type():
    bad = np.random.random((3, 3, 3)).astype('uint8')
    with pytest.raises(ValueError) as exc:
        saturate_rgb(bad, 1.1)
    assert 'dtype mismatch' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert_arr(bad, 'RGB', 'LCH')
    assert 'dtype mismatch' in str(exc.value)


def test_bad_colorspace():
    with pytest.raises(ValueError) as exc:
        convert(0.1, 0.1, 0.1, src='FOO', dst='RGB')
    assert 'is not in list' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        convert(0.1, 0.1, 0.1, src='RGB', dst='FOO')
    assert 'is not in list' in str(exc.value)
