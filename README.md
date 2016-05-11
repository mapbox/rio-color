# rio-color

[![Build Status](https://travis-ci.org/mapbox/rio-color.svg)](https://travis-ci.org/mapbox/rio-color)
[![Coverage Status](https://coveralls.io/repos/mapbox/rio-color/badge.svg?branch=master&service=github)](https://coveralls.io/github/mapbox/rio-color?branch=master)

Color-oriented operations for `rasterio`/`rio`.

## Goals

We want to supply a baseline selection of esthetics-oriented image operations for numpy/rasterio, exposed as much as possible through `rio`. Some functions may be trivial (gamma) or already implemented elsewhere (for example, in `skimage`), but we want versions of them that are standard and light, without big dependencies.

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

### `rio_color.operations`

The following functions accept and return numpy `ndarrays`. The arrays are assumed to be scaled 0 to 1. In some cases, the input array is assumed to be in a certain colorspace with the axis order as (bands, columns, rows); other image processing software may use the (columns, rows, bands) axis order.

* `sigmoidal(arr, contrast, bias)`
* `gamma(arr, g)`
* `saturation(rgb, proportion)`
* `simple_atmo(rgb, haze, contrast, bias)`

There is one function in the `rio_color.operations` module which doesn't manipulate arrays:
`parse_operations`. This function takes an *operations string* and
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

  Operations will be applied to the src image in the specified order. Each
  operation should be a single quoted argument.

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

  BANDS are specified as a single arg

      `123` or `RGB` or `rgb` are all equivalent

  Example:

      rio color -d uint8 -j 4 input.tif output.tif \
          gamma 3 0.95 sigmoidal 1,2,3 35 0.13


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
