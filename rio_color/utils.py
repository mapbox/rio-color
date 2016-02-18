import numpy as np

math_type = np.float32

epsilon = np.finfo(math_type).eps


def to_math_type(arr, dtype):
    '''Convert an array from uint16 to 0..1, scaling down linearly'''
    max_int = np.iinfo(dtype).max
    return arr.astype(math_type) / max_int


def scale_dtype(arr, dtype):
    '''Convert an array from 0..1 to uint16, scaling up linearly'''
    max_int = np.iinfo(dtype).max
    return (arr * max_int).astype(dtype)
