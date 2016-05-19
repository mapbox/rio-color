# rio-color

[![Build Status](https://travis-ci.org/mapbox/rio-color.svg)](https://travis-ci.org/mapbox/rio-color)
[![Coverage Status](https://coveralls.io/repos/mapbox/rio-color/badge.svg?branch=master&service=github)](https://coveralls.io/github/mapbox/rio-color?branch=master)

A rasterio plugin for applying basic color-oriented image operations to geospatial rasters.

## Goals

* **No heavy dependencies**: rio-color is purposefully limited in scope to remain lightweight
* **Use the image structure**: By iterating over the internal blocks of the input image, we keep memory usage low and predictable while gaining the abililty to
* **Use multiple cores**: thanks to [rio-mucho](https://github.com/mapbox/rio-mucho)
* **Retain all the GeoTIFF info and TIFF structure**: nothing is lost. A GeoTIFF input → GeoTIFF output with the same georeferencing, internal tiling, compression, nodata values, etc.
* **Efficient colorspace conversions**: the intesive math is written in highly optimized C functions and for use with scalars and numpy arrays.
* **CLI and Python module**: accessing the functionality as a python module that can act on in-memory numpy arrays opens up new opportunities for composing this with other array operations without using intermediate files.

## Operations


**Gamma** adjustment adjusts RGB values according to a power law, effectively brightening or darkening the midtones. It can be very effective in satellite imagery for reducing atmospheric haze in the blue and green bands.

**Sigmoidal** contrast adjustment can alter the contrast and brightness of an image in a way that
matches human's non-linear visual perception. It works well to increase contrast without blowing out the very dark shadows or already-bright parts of the image.

**Saturation** can be thought of as the "colorfulness" of a pixel. Highly saturated colors are intense and almost cartoon-like, low saturation is more muted, closer to black and white. You can adjust saturation independently of brightness and hue but the data must be transformed into a different color space.


![animated](https://cloud.githubusercontent.com/assets/1151287/15330468/f5cefc38-1c2a-11e6-855d-8bb0f4158ca7.gif)


   
## Install

We highly recommend installing in a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/). Once activated, 

```
pip install -U pip
pip install rio-color
```

Or if you want to install from source
```
git checkout https://github.com/mapbox/rio-color.git
cd rio-color
pip install -U pip
pip install -r requirements-dev.txt
pip install -e .
```

## Python API

#### `rio_color.operations`

The following functions accept and return numpy `ndarrays`. The arrays are assumed to be scaled 0 to 1. In some cases, the input array is assumed to be in the RGB colorspace.

All arrays use rasterio ordering with the shape as (bands, columns, rows). Be aware that other image processing software may use the (columns, rows, bands) axis order.

* `sigmoidal(arr, contrast, bias)`
* `gamma(arr, g)`
* `saturation(rgb, proportion)`
* `simple_atmo(rgb, haze, contrast, bias)`

The `rio_color.operations.parse_operations` function takes an *operations string* and
returns a list of python functions which can be applied to an array.

```
ops = "gamma b 1.85, gamma rg 1.95, sigmoidal rgb 35 0.13, saturation 1.15"

assert arr.shape[0] == 3
assert arr.min() >= 0
assert arr.max() <= 1

for func in parse_operations(ops):
    arr = func(arr)
```

This provides a tiny domain specific language (DSL) to allow you
to compose ordered chains of image manipulations using the above operations.
For more information on operation strings, see the `rio color` command line help.

#### `rio_color.colorspace`

The `colorspace` module provides functions for converting scalars and numpy arrays between different colorspaces.

```python
>>> from rio_color.colorspace import ColorSpace as cs  # enum defining available color spaces
>>> from rio_color.colorspace import convert, convert_arr
>>> convert_arr(array, src=cs.rgb, dst=cs.lch) # for arrays
...
>>> convert(r, g, b, src=cs.rgb, dst=cs.lch)  # for scalars
...
>>> dict(cs.__members__)  # can convert to/from any of these color spaces
{'lab': <ColorSpace.lab: 2>,
 'lch': <ColorSpace.lch: 3>,
 'rgb': <ColorSpace.rgb: 0>,
 'xyz': <ColorSpace.xyz: 1>}
```

## Command Line Interface

Rio color provides two command line interfaces:

### `rio color`

A general-purpose color correction tool to perform gamma, contrast and saturation adjustments.

The advantages over Imagemagick `convert`: `rio color` is
geo-aware, retains the profile of the source image, iterates efficiently over interal tiles
and can use multiple cores.

```
Usage: rio color [OPTIONS] SRC_PATH DST_PATH OPERATIONS...

  Color correction

  Operations will be applied to the src image in the specified order.

  Available OPERATIONS include:

      "gamma BANDS VALUE"
          Applies a gamma curve, brightening or darkening midtones.
          VALUE > 1 brightens the image.

      "sigmoidal BANDS CONTRAST BIAS"
          Adjusts the contrast and brightness of midtones.
          BIAS > 0.5 darkens the image.

      "saturation PROPORTION"
          Controls the saturation in LCH color space.
          PROPORTION = 0 results in a grayscale image
          PROPORTION = 1 results in an identical image
          PROPORTION = 2 is likely way too saturated

  BANDS are specified as a single arg, no delimiters

      `123` or `RGB` or `rgb` are all equivalent

  Example:

      rio color -d uint8 -j 4 input.tif output.tif \
          gamma 3 0.95, sigmoidal rgb 35 0.13


Options:
  -j, --jobs INTEGER              Number of jobs to run simultaneously, Use -1
                                  for all cores, default: 1
  -d, --out-dtype [uint8|uint16]  Integer data type for output data, default:
                                  same as input
  --co NAME=VALUE                 Driver specific creation options.See the
                                  documentation for the selected output driver
                                  for more information.
  --help                          Show this message and exit.
```

Example:

```
$ rio color -d uint8 -j 4 rgb.tif test.tif \
    gamma G 1.85 gamma B 1.95 sigmoidal RGB 35 0.13 saturation 1.15
```

![screen shot 2016-02-17 at 12 18 47 pm](https://cloud.githubusercontent.com/assets/1151287/13116122/0f7f5f20-d571-11e5-82e7-9cc65c443972.png)

### `rio atmos`

Provides a higher-level tool for general atmospheric correction of satellite imagery using
a proven set of operations to adjust for haze.

```
Usage: rio atmos [OPTIONS] SRC_PATH DST_PATH

  Atmospheric correction

Options:
  -a, --atmo FLOAT                How much to dampen cool colors, thus cutting
                                  through haze. 0..1 (0 is none), default:
                                  0.03.
  -c, --contrast FLOAT            Contrast factor to apply to the scene.
                                  -infinity..infinity(0 is none), default: 10.
  -b, --bias FLOAT                Skew (brighten/darken) the output. Lower
                                  values make it brighter. 0..1 (0.5 is none),
                                  default: 0.15
  -d, --out-dtype [uint8|uint16]  Integer data type for output data, default:
                                  same as input
  --as-color                      Prints the equivalent rio color command to
                                  stdout.Does NOT run either command, SRC_PATH
                                  will not be created
  -j, --jobs INTEGER              Number of jobs to run simultaneously, Use -1
                                  for all cores, default: 1
  --co NAME=VALUE                 Driver specific creation options.See the
                                  documentation for the selected output driver
                                  for more information.
  --help                          Show this message and exit.
```
