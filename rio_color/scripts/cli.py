import click
import rasterio
from rio_color import color_worker
import riomucho


@click.command('color')
@click.option(
    '--atmo', '-a', type=click.FLOAT, default=0.03,
    help='How much to dampen cool colors, thus cutting through haze. 0..1 (0 is none), default 0.03.')
@click.option(
    '--contrast', '-c', type=click.FLOAT, default=10,
    help='Contrast factor to apply to the scene. -infinity..infinity (0 is none), default 10.'
)
@click.option(
    '--bias', '-b', type=click.FLOAT, default=15,
    help='Skew (brighten/darken) the output. Lower values make it brighter. 0..100 (50 is none), default 15.'
)
@click.option('--max-procs', '-j', type=int, default=8)
@click.option('--out-dtype')
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.pass_context
def simple_color(ctx, atmo, contrast, bias, max_procs, out_dtype,
                 src_path, dst_path):
    with rasterio.open(src_path) as src:
        opts = src.meta.copy()
        kwds = src.profile.copy()
        windows = [(window, ij) for ij, window in src.block_windows()]

    opts.update(**kwds)

    colorer_args = {
        'atmo': atmo,
        'contrast': contrast,
        'bias': bias / 100.0,
        'out_dtype': out_dtype if out_dtype else opts['dtype']
    }

    # Helpful for debugging
    # for window, ij in windows:
    #     rasters = [rasterio.open(src_path)]
    #     color_worker(rasters, window, ij, colorer_args)

    with riomucho.RioMucho(
        [src_path],
        dst_path,
        color_worker,
        windows=windows,
        options=opts,
        global_args=colorer_args,
        mode="manual_read"
    ) as mucho:
        mucho.run(max_procs)

if __name__ == '__main__':
    simple_color()
