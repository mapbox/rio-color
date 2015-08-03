# rio-color

[![Build Status](https://travis-ci.org/mapbox/rio-color.svg)](https://travis-ci.org/mapbox/rio-color)
[![Coverage Status](https://coveralls.io/repos/mapbox/rio-color/badge.svg?branch=master&service=github)](https://coveralls.io/github/mapbox/rio-color?branch=master)

Color-oriented operations for `rasterio`/`rio`.

## Goals

We want to supply a baseline selection of esthetics-oriented image operations for numpy/rasterio, exposed as much as possible through `rio`. Some functions may be trivial (gamma) or already implemented elsewhere (for example, in `skimage`), but we want versions of them that are standard and light, without big dependencies.

## Supported operations

- *gamma* applies a gamma curve, brightening or darkening an image's midtones. It's expressed in the conventional way for image processing, where a gamma larger than 1 brightens the image.

- *sigmoidal contrast* increases (or decreases) midtone contrast, with an optional bias that brightens or darkens midtones at the same time.

