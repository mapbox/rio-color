import click
import rasterio as rio
import rio_color as rico

@click.command('color')
@click.option(
  '--atmo',
  '-a',
  type=click.FLOAT,
  default=0.03,
  help='How much to dampen cool colors, thus cutting through haze. 0..1 (0 is none), default 0.03.')

@click.option(
  '--contrast',
  '-c',
  type=click.FLOAT,
  default=10,
  help='Contrast factor to apply to the scene. -infinity..infinity (0 is none), default 10.'
)

@click.option(
  '--bias',
  '-b',
  type=click.FLOAT,
  default=15,
  help='Skew (brighten/darken) the output. Lower values make it brighter. 0..100 (50 is none), default 15.'
)

@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.pass_context
def simple_color(ctx, atmo, contrast, bias, src_path, dst_path):

  # todo: test that image is 16 bits, 3 bands, etc.
  # todo: think about mask/alpha
  bidxs = 1, 2, 3
  
  bias = bias/100.0

  with rio.open(src_path) as src:
    src_meta = src.meta
    src_meta.update(photometric='RGB')
    src_meta.update(transform=src_meta['affine'])

    with rio.open(dst_path, 'w', **src_meta) as dst:
    
      rgb = src.read()
    
      rgb_adj = rico.simple_atmo(
        rgb,
        atmo,
        contrast,
        bias)
		
      for bidx in bidxs:
        dst.write(
          rgb_adj[bidx-1],
          bidx)

if __name__ == '__main__':
  simple_color()