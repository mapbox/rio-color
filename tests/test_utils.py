import numpy as np
import pytest

from rio_color.utils import to_math_type, math_type, scale_dtype

@pytest.fixture
def arr():
    return np.array([
        [[1, 2],
         [3, 4]],
        [[5, 6],
         [7, 8]],
        [[9, 10],
         [11, 12]],
        [[0, 0],
         [0, 0]],
    ]).astype('uint8') * 10


def test_to_math_type(arr):
    x = to_math_type(arr)
    assert x.dtype == math_type
    assert x.max() <= 1.0
    assert x.min() >= 0.0


def test_scale_dtype():
    arr = np.array([0.0, 1.0]).astype(math_type)
    x = scale_dtype(arr, 'uint8')
    assert x.max() == 255
    assert x.min() == 0
    x = scale_dtype(arr, 'uint16')
    assert x.max() == 65535
    assert x.min() == 0


def test_scale_round_trip(arr):
    x = to_math_type(arr)
    y = scale_dtype(x, arr.dtype)
    assert np.array_equal(arr, y)
