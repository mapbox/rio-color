from .operations import parse_operations, simple_atmo
from .utils import to_math_type, scale_dtype

# Rio workers

def atmos_worker(srcs, window, ij, args):
    src = srcs[0]
    rgb = src.read(window=window)
    rgb = to_math_type(rgb)

    atmos = simple_atmo(
        rgb,
        args['atmo'],
        args['contrast'],
        args['bias'])

    # should be scaled 0 to 1, scale to outtype
    return scale_dtype(atmos, args['out_dtype'])


def color_worker(srcs, window, ij, args):
    src = srcs[0]
    arr = src.read(window=window)
    arr = to_math_type(arr)

    for func in parse_operations(args['ops_string']):
        arr = func(arr)

    # scaled 0 to 1, now scale to outtype
    return scale_dtype(arr, args['out_dtype'])
