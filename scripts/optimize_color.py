#!/usr/bin/env python
from __future__ import division, print_function

import time
import random
import sys
from collections import OrderedDict

from simanneal import Annealer
import click
import numpy as np
import rasterio

from rio_color.operations import parse_operations
from rio_color.utils import to_math_type


def time_string(seconds):
    """Returns time in seconds as a string formatted HHHH:MM:SS."""
    s = int(round(seconds))  # round to nearest second
    h, s = divmod(s, 3600)   # get hours and remainder
    m, s = divmod(s, 60)     # split remainder into minutes and seconds
    return '%4i:%02i:%02i' % (h, m, s)


class ColorEstimator(Annealer):

    keys = "gamma_red,gamma_green,gamma_blue,contrast,bias".split(',')

    def __init__(self, source, reference, state=None):
        self.src = source.copy()
        self.ref = reference.copy()
        if not state:
            params = OrderedDict(
                gamma_red=1.0,
                gamma_green=1.0,
                gamma_blue=1.0,
                contrast=10,
                bias=0.5,
                saturation=1.0)
        else:
            if self._validate(state):
                params = state
            else:
                raise ValueError('invalid state')

        super(ColorEstimator, self).__init__(params)

    def validate(self):
        # todo validate values bt 0..1
        for k in self.keys:
            if k not in self.state:
                return False

    def move(self):
        k = random.choice(self.keys)
        multiplier = random.choice((0.9, 1.1))

        invalid_key = True
        while invalid_key:
            # make sure bias doesn't exceed 1.0
            if k == 'bias':
                if self.state[k] > 0.909:
                    k = random.choice(self.keys)
                    continue

            invalid_key = False

        newval = self.state[k] * multiplier
        self.state[k] = newval

    def cmd(self, state):
        ops = "gamma r {gamma_red}, gamma g {gamma_green}, gamma b {gamma_blue}, " \
              "sigmoidal rgb {contrast} {bias}".format(
                  **state)
        return ops

    def energy(self):
        arr = self.src.copy()
        ops = self.cmd(self.state)

        for func in parse_operations(ops):
            arr = func(arr)

        scores = [histogram_distance(self.ref[i], arr[i])
                  for i in range(3)]
        return sum(scores)

    def update(self, step, T, E, acceptance, improvement):
        elapsed = time.time() - self.start
        if step == 0:
            print(' Temperature        Energy    Accept   Improve     Elapsed   Remaining',
                  file=sys.stderr)
            print('\r%12.5f  %12.2f                      %s            ' %
                  (T, E, time_string(elapsed)), file=sys.stderr, end="\r"),
            sys.stderr.flush()
        else:
            remain = (self.steps - step) * (elapsed / step)
            print('\r%12.5f  %12.2f  %7.2f%%  %7.2f%%  %s  %s\r' %
                  (T, E, 100.0 * acceptance, 100.0 * improvement,
                   time_string(elapsed), time_string(remain)), file=sys.stderr, end="\r"),
            sys.stderr.flush()


def histogram_distance(arr1, arr2, bins=None):
    """ This function returns the sum of the squared error
    Parameters:
        two arrays constrained to 0..1

    Returns:
        sum of the squared error between the histograms
    """
    eps = 1e-6
    assert arr1.min() > 0-eps
    assert arr1.max() < 1+eps
    assert arr2.min() > 0-eps
    assert arr2.max() < 1+eps

    if not bins:
        bins = [x / 10 for x in range(11)]
    hist1 = np.histogram(arr1, bins=bins)[0] / arr1.size
    hist2 = np.histogram(arr2, bins=bins)[0] / arr2.size

    assert abs(hist1.sum() - 1.0) < eps
    assert abs(hist2.sum() - 1.0) < eps

    sqerr = (hist1 - hist2)**2
    return sqerr.sum()

def calc_downsample(w, h, target=400):
    if w > h:
        return h / target
    elif h >= w:
        return w / target

@click.command()
@click.argument('source')
@click.argument('reference')
@click.option('--downsample', '-d', type=int, default=None)
@click.option('--steps', '-s', type=int, default=5000)
def main(source, reference, downsample, steps):
    """Given a source image and a reference image,
    Find the rio color formula which results in an
    output with similar histogram to the reference image.

    Uses simulated annealing to determine optimal settings.

    Increase the --downsample option to speed things up.
    Increase the --steps to get better results (longer runtime).
    """

    with rasterio.open(source) as src:
        if downsample is None:
            ratio = calc_downsample(src.width, src.height)
        else:
            ratio = downsample
        w = int(src.width // ratio)
        h = int(src.height // ratio)
        rgb = src.read((1, 2, 3), out_shape=(3, h, w))
        orig_rgb = to_math_type(rgb)

    with rasterio.open(reference) as ref:
        if downsample is None:
            ratio = calc_downsample(ref.width, ref.height)
        else:
            ratio = downsample
        w = int(ref.width / ratio)
        h = int(ref.height / ratio)
        rgb = ref.read((1, 2, 3), out_shape=(3, h, w))
        ref_rgb = to_math_type(rgb)

    est = ColorEstimator(orig_rgb, ref_rgb)

    schedule = dict(
        tmax=1.0,  # Max (starting) temperature
        tmin=1e-9,      # Min (ending) temperature
        steps=steps,   # Number of iterations
        updates=steps/20   # Number of updates (by default an update prints to stdout)
    )

    est.set_schedule(schedule)
    optimal, score = est.anneal()
    optimal['energy'] = score
    ops = est.cmd(optimal)
    click.echo('rio color -j4 {} {} {}'.format(
        source, '/tmp/output.tif', ops))


if __name__ == "__main__":
    main()
