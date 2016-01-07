import click
import rasterio as rio
import rio_color as rico
import riomucho


def colorer(rgb, window, ij, args):
    return rico.simple_atmo(
        rgb[0],
        args['atmo'],
        args['contrast'],
        args['bias'])


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
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.pass_context
def simple_color(ctx, atmo, contrast, bias, src_path, dst_path):
    with rio.open(src_path) as src:
        opts = src.meta.copy()
        kwds = src.profile.copy()
    opts.update(**kwds)

    colorer_args = {
        'atmo': atmo,
        'contrast': contrast,
        'bias': bias / 100.0
    }

    with riomucho.RioMucho(
        [src_path],
        dst_path,
        colorer,
        options=opts,
        global_args=colorer_args
    ) as mucho:
        mucho.run(8)

if __name__ == '__main__':
    simple_color()
