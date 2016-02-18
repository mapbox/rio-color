import click
import rasterio
from rio_color.workers import atmos_worker, color_worker
from rio_color.operations import parse_operations
import riomucho


def validate_bands(bandstr, count):
    try:
        bands = [int(x) for x in bandstr.split(",")]
        assert min(bands) > 0
        assert max(bands) <= count
    except (AssertionError, ValueError):
        raise click.UsageError(
            "Invalid bands: '{}' (requires comma-separated ints)".format(bandstr))
    return bands


@click.command('color')
@click.option('--max-procs', '-j', type=int, default=1)
@click.option('--out-dtype', '-d', type=click.Choice(['uint8', 'uint16']))
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.argument('operations', nargs=-1)
@click.pass_context
def color(ctx, max_procs, out_dtype, src_path, dst_path, operations):
    """Color correction

Operations will be applied to the src image in the specified order.
Each operation should be a single quoted argument.

Available OPERATIONS include:

\b
    "gamma BANDS VALUE"
        Applies a gamma curve, brighten or darken midtones.
        VALUE > 1 brightens the image.

\b
    "sigmoidal BANDS CONTRAST BIAS"
        Adjusts the contrast and brightness of midtones.

\b
    "saturation PERCENTAGE"
        Controls the saturation in HSV color space.
        PERCENTAGE = 0 results in a grayscale image

BANDS are specified as a comma-separated list of band numbers or letters

\b
    `1,2,3` or `R,G,B` or `r,g,b` are all equivalent

Example:

\b
    rio color -d uint8 -j 4 input.tif output.tif \\
        "gamma 3 0.95" "sigmoidal 1,2,3 35 0.13"
    """
    with rasterio.open(src_path) as src:
        opts = src.meta.copy()
        kwds = src.profile.copy()
        windows = [(window, ij) for ij, window in src.block_windows()]

    opts.update(**kwds)
    opts['transform'] = opts['affine']

    out_dtype = out_dtype if out_dtype else opts['dtype']
    opts['dtype'] = out_dtype

    # Just run this for validation this time
    # parsing will be run again within the worker
    # where its returned value will be used
    try:
        list(parse_operations(operations, opts['count']))
    except ValueError as e:
        raise click.UsageError(e.message)

    args = {
        'operations': operations,
        'out_dtype': out_dtype
    }

    if max_procs > 1:
        with riomucho.RioMucho(
            [src_path],
            dst_path,
            color_worker,
            windows=windows,
            options=opts,
            global_args=args,
            mode="manual_read"
        ) as mucho:
            mucho.run(max_procs)
    else:
        with rasterio.open(dst_path, 'w', **opts) as dest:
            with rasterio.open(src_path) as src:
                rasters = [src]
                for window, ij in windows:
                    arr = color_worker(rasters, window, ij, args)
                    dest.write(arr, window=window)


@click.command('atmos')
@click.option('--atmo', '-a', type=click.FLOAT, default=0.03,
              help="How much to dampen cool colors, thus cutting through "
                   "haze. 0..1 (0 is none), default 0.03.")
@click.option('--contrast', '-c', type=click.FLOAT, default=10,
              help="Contrast factor to apply to the scene. -infinity..infinity"
                   "(0 is none), default 10.")
@click.option('--bias', '-b', type=click.FLOAT, default=15,
              help="Skew (brighten/darken) the output. Lower values make it "
                   "brighter. 0..100 (50 is none), default 15.")
@click.option('--max-procs', '-j', type=int, default=8)
@click.option('--out-dtype', '-d', type=click.Choice(['uint8', 'uint16']))
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.pass_context
def atmos(ctx, atmo, contrast, bias, max_procs, out_dtype,
          src_path, dst_path):
    """Atmospheric correction
    """
    with rasterio.open(src_path) as src:
        opts = src.meta.copy()
        kwds = src.profile.copy()
        windows = [(window, ij) for ij, window in src.block_windows()]

    opts.update(**kwds)
    opts['transform'] = opts['affine']

    out_dtype = out_dtype if out_dtype else opts['dtype']
    opts['dtype'] = out_dtype

    args = {
        'atmo': atmo,
        'contrast': contrast,
        'bias': bias / 100.0,
        'out_dtype': out_dtype
    }

    if max_procs > 1:
        with riomucho.RioMucho(
            [src_path],
            dst_path,
            atmos_worker,
            windows=windows,
            options=opts,
            global_args=args,
            mode="manual_read"
        ) as mucho:
            mucho.run(max_procs)
    else:
        with rasterio.open(dst_path, 'w', **opts) as dest:
            with rasterio.open(src_path) as src:
                rasters = [src]
                for window, ij in windows:
                    arr = color_worker(rasters, window, ij, args)
                    dest.write(arr, window=window)
