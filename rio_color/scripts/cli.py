import click

import rasterio
from rasterio.rio.options import creation_options
from rio_color.workers import atmos_worker, color_worker
from rio_color.operations import parse_operations, simple_atmo_opstring
import riomucho


jobs_opt = click.option(
    '--jobs', '-j', type=int, default=1,
    help="Number of jobs to run simultaneously, Use -1 for all cores, default: 1")


def check_jobs(jobs):
    if jobs == 0:
        raise click.UsageError("Jobs must be >= 1 or == -1")
    elif jobs < 0:
        import multiprocessing
        jobs = multiprocessing.cpu_count()
    return jobs


@click.command('color')
@jobs_opt
@click.option('--out-dtype', '-d', type=click.Choice(['uint8', 'uint16']),
              help="Integer data type for output data, default: same as input")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.argument('operations', nargs=-1, required=True)
@click.pass_context
@creation_options
def color(ctx, jobs, out_dtype, src_path, dst_path, operations,
          creation_options):
    """Color correction

Operations will be applied to the src image in the specified order.

Available OPERATIONS include:

\b
    "gamma BANDS VALUE"
        Applies a gamma curve, brightening or darkening midtones.
        VALUE > 1 brightens the image.

\b
    "sigmoidal BANDS CONTRAST BIAS"
        Adjusts the contrast and brightness of midtones.
        BIAS > 0.5 darkens the image.

\b
    "saturation PROPORTION"
        Controls the saturation in LCH color space.
        PROPORTION = 0 results in a grayscale image
        PROPORTION = 1 results in an identical image
        PROPORTION = 2 is likely way too saturated

BANDS are specified as a single arg, no delimiters

\b
    `123` or `RGB` or `rgb` are all equivalent

Example:

\b
    rio color -d uint8 -j 4 input.tif output.tif \\
        gamma 3 0.95, sigmoidal rgb 35 0.13
    """
    with rasterio.open(src_path) as src:
        opts = src.profile.copy()
        windows = [(window, ij) for ij, window in src.block_windows()]

    opts.update(**creation_options)
    opts['transform'] = opts['affine']

    out_dtype = out_dtype if out_dtype else opts['dtype']
    opts['dtype'] = out_dtype

    args = {
        'ops_string': ' '.join(operations),
        'out_dtype': out_dtype
    }
    # Just run this for validation this time
    # parsing will be run again within the worker
    # where its returned value will be used
    try:
        ops = parse_operations(args['ops_string'])
    except ValueError as e:
        raise click.UsageError(str(e))

    jobs = check_jobs(jobs)

    if jobs > 1:
        with riomucho.RioMucho(
            [src_path],
            dst_path,
            color_worker,
            windows=windows,
            options=opts,
            global_args=args,
            mode="manual_read"
        ) as mucho:
            mucho.run(jobs)
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
                   "haze. 0..1 (0 is none), default: 0.03.")
@click.option('--contrast', '-c', type=click.FLOAT, default=10,
              help="Contrast factor to apply to the scene. -infinity..infinity"
                   "(0 is none), default: 10.")
@click.option('--bias', '-b', type=click.FLOAT, default=0.15,
              help="Skew (brighten/darken) the output. Lower values make it "
                   "brighter. 0..1 (0.5 is none), default: 0.15")
@click.option('--out-dtype', '-d', type=click.Choice(['uint8', 'uint16']),
              help="Integer data type for output data, default: same as input")
@click.option('--as-color', is_flag=True, default=False,
              help="Prints the equivalent rio color command to stdout."
                   "Does NOT run either command, SRC_PATH will not be created")
@click.argument('src_path', required=True)
@click.argument('dst_path', type=click.Path(exists=False))
@jobs_opt
@creation_options
@click.pass_context
def atmos(ctx, atmo, contrast, bias, jobs, out_dtype,
          src_path, dst_path, creation_options, as_color):
    """Atmospheric correction
    """
    if as_color:
        click.echo("rio color {} {} {}".format(
            src_path, dst_path, simple_atmo_opstring(atmo, contrast, bias)))
        exit(0)

    with rasterio.open(src_path) as src:
        opts = src.profile.copy()
        windows = [(window, ij) for ij, window in src.block_windows()]

    opts.update(**creation_options)
    opts['transform'] = opts['affine']

    out_dtype = out_dtype if out_dtype else opts['dtype']
    opts['dtype'] = out_dtype

    args = {
        'atmo': atmo,
        'contrast': contrast,
        'bias': bias,
        'out_dtype': out_dtype
    }

    jobs = check_jobs(jobs)

    if jobs > 1:
        with riomucho.RioMucho(
            [src_path],
            dst_path,
            atmos_worker,
            windows=windows,
            options=opts,
            global_args=args,
            mode="manual_read"
        ) as mucho:
            mucho.run(jobs)
    else:
        with rasterio.open(dst_path, 'w', **opts) as dest:
            with rasterio.open(src_path) as src:
                rasters = [src]
                for window, ij in windows:
                    arr = atmos_worker(rasters, window, ij, args)
                    dest.write(arr, window=window)
