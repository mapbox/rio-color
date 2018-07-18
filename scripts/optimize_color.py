#!/usr/bin/env python

"""Example script"""

from __future__ import division, print_function

import random
import time

from simanneal import Annealer
import click
import numpy as np
import rasterio

from rasterio.plot import reshape_as_image
from rio_color.operations import parse_operations
from rio_color.utils import to_math_type


def time_string(seconds):
    """Returns time in seconds as a string formatted HHHH:MM:SS."""
    s = int(round(seconds))  # round to nearest second
    h, s = divmod(s, 3600)  # get hours and remainder
    m, s = divmod(s, 60)  # split remainder into minutes and seconds
    return "%2i:%02i:%02i" % (h, m, s)


def progress_report(
    curr, best, curr_score, best_score, step, totalsteps, accept, improv, elaps, remain
):
    """Report progress"""
    text = """
Current Formula    {curr}   (hist distance {curr_score})
Best Formula       {best}   (hist distance {best_score})
Step {step} of {totalsteps}
Acceptance Rate : {accept} %
Improvement Rate: {improv} %
Time  {elaps} ( {remain} Remaing)""".format(
        **locals()
    )
    return text


# Plot globals
fig = None
txt = None
imgs = []


class ColorEstimator(Annealer):
    """Optimizes color using simulated annealing"""

    keys = "gamma_red,gamma_green,gamma_blue,contrast".split(",")

    def __init__(self, source, reference, state=None):
        """Create a new instance"""
        self.src = source.copy()
        self.ref = reference.copy()

        if not state:
            params = dict(gamma_red=1.0, gamma_green=1.0, gamma_blue=1.0, contrast=10)
        else:
            if self._validate(state):
                params = state
            else:
                raise ValueError("invalid state")

        super(ColorEstimator, self).__init__(params)

    def validate(self):
        """Validate keys."""
        # todo validate values bt 0..1
        for k in self.keys:
            if k not in self.state:
                return False

    def move(self):
        """Create a state change."""
        k = random.choice(self.keys)
        multiplier = random.choice((0.95, 1.05))

        invalid_key = True
        while invalid_key:
            # make sure bias doesn't exceed 1.0
            if k == "bias":
                if self.state[k] > 0.909:
                    k = random.choice(self.keys)
                    continue

            invalid_key = False

        newval = self.state[k] * multiplier
        self.state[k] = newval

    def cmd(self, state):
        """Get color formula representation of the state."""
        ops = (
            "gamma r {gamma_red:.2f}, gamma g {gamma_green:.2f}, gamma b {gamma_blue:.2f}, "
            "sigmoidal rgb {contrast:.2f} 0.5".format(**state)
        )
        return ops

    def apply_color(self, arr, state):
        """Apply color formula to an array."""
        ops = self.cmd(state)
        for func in parse_operations(ops):
            arr = func(arr)
        return arr

    def energy(self):
        """Calculate state's energy."""
        arr = self.src.copy()
        arr = self.apply_color(arr, self.state)

        scores = [histogram_distance(self.ref[i], arr[i]) for i in range(3)]

        # Important: scale by 100 for readability
        return sum(scores) * 100

    def to_dict(self):
        """Serialize as a dict."""
        return dict(best=self.best_state, current=self.state)

    def update(self, step, T, E, acceptance, improvement):
        """Print progress."""
        if acceptance is None:
            acceptance = 0
        if improvement is None:
            improvement = 0
        if step > 0:
            elapsed = time.time() - self.start
            remain = (self.steps - step) * (elapsed / step)
            # print('Time {}  ({} Remaing)'.format(time_string(elapsed), time_string(remain)))
        else:
            elapsed = 0
            remain = 0

        curr = self.cmd(self.state)
        curr_score = float(E)
        best = self.cmd(self.best_state)
        best_score = self.best_energy
        report = progress_report(
            curr,
            best,
            curr_score,
            best_score,
            step,
            self.steps,
            acceptance * 100,
            improvement * 100,
            time_string(elapsed),
            time_string(remain),
        )
        print(report)

        if fig:
            imgs[1].set_data(
                reshape_as_image(self.apply_color(self.src.copy(), self.state))
            )
            imgs[2].set_data(
                reshape_as_image(self.apply_color(self.src.copy(), self.best_state))
            )
            if txt:
                txt.set_text(report)
            fig.canvas.draw()


def histogram_distance(arr1, arr2, bins=None):
    """ This function returns the sum of the squared error
    Parameters:
        two arrays constrained to 0..1

    Returns:
        sum of the squared error between the histograms
    """
    eps = 1e-6
    assert arr1.min() > 0 - eps
    assert arr1.max() < 1 + eps
    assert arr2.min() > 0 - eps
    assert arr2.max() < 1 + eps

    if not bins:
        bins = [x / 10 for x in range(11)]
    hist1 = np.histogram(arr1, bins=bins)[0] / arr1.size
    hist2 = np.histogram(arr2, bins=bins)[0] / arr2.size

    assert abs(hist1.sum() - 1.0) < eps
    assert abs(hist2.sum() - 1.0) < eps

    sqerr = (hist1 - hist2) ** 2
    return sqerr.sum()


def calc_downsample(w, h, target=400):
    """Calculate downsampling value."""
    if w > h:
        return h / target
    elif h >= w:
        return w / target


@click.command()
@click.argument("source")
@click.argument("reference")
@click.option("--downsample", "-d", type=int, default=None)
@click.option("--steps", "-s", type=int, default=5000)
@click.option("--plot/--no-plot", default=True)
def main(source, reference, downsample, steps, plot):
    """Given a source image and a reference image,
    Find the rio color formula which results in an
    output with similar histogram to the reference image.

    Uses simulated annealing to determine optimal settings.

    Increase the --downsample option to speed things up.
    Increase the --steps to get better results (longer runtime).
    """
    global fig, txt, imgs

    click.echo("Reading source data...", err=True)
    with rasterio.open(source) as src:
        if downsample is None:
            ratio = calc_downsample(src.width, src.height)
        else:
            ratio = downsample
        w = int(src.width // ratio)
        h = int(src.height // ratio)
        rgb = src.read((1, 2, 3), out_shape=(3, h, w))
        orig_rgb = to_math_type(rgb)

    click.echo("Reading reference data...", err=True)
    with rasterio.open(reference) as ref:
        if downsample is None:
            ratio = calc_downsample(ref.width, ref.height)
        else:
            ratio = downsample
        w = int(ref.width / ratio)
        h = int(ref.height / ratio)
        rgb = ref.read((1, 2, 3), out_shape=(3, h, w))
        ref_rgb = to_math_type(rgb)

    click.echo("Annealing...", err=True)
    est = ColorEstimator(orig_rgb, ref_rgb)

    if plot:
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(20, 10))
        fig.suptitle("Color Formula Optimization", fontsize=18, fontweight="bold")
        txt = fig.text(0.02, 0.05, "foo", family="monospace", fontsize=16)
        type(txt)
        axs = (
            fig.add_subplot(1, 4, 1),
            fig.add_subplot(1, 4, 2),
            fig.add_subplot(1, 4, 3),
            fig.add_subplot(1, 4, 4),
        )
        fig.tight_layout()
        axs[0].set_title("Source")
        axs[1].set_title("Current Formula")
        axs[2].set_title("Best Formula")
        axs[3].set_title("Reference")
        imgs.append(axs[0].imshow(reshape_as_image(est.src)))
        imgs.append(axs[1].imshow(reshape_as_image(est.src)))
        imgs.append(axs[2].imshow(reshape_as_image(est.src)))
        imgs.append(axs[3].imshow(reshape_as_image(est.ref)))
        fig.show()

    schedule = dict(
        tmax=25.0,  # Max (starting) temperature
        tmin=1e-4,  # Min (ending) temperature
        steps=steps,  # Number of iterations
        updates=steps / 20,  # Number of updates
    )

    est.set_schedule(schedule)
    est.save_state_on_exit = False
    optimal, score = est.anneal()
    optimal["energy"] = score
    ops = est.cmd(optimal)
    click.echo("rio color -j4 {} {} {}".format(source, "/tmp/output.tif", ops))


if __name__ == "__main__":
    main()
