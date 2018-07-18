import os

from click import UsageError
from click.testing import CliRunner
import numpy as np
import pytest
import rasterio
from rasterio.enums import Compression

from rio_color.scripts.cli import color, atmos, check_jobs


def equal(r1, r2):
    with rasterio.open(r1) as src1:
        with rasterio.open(r2) as src2:
            return np.array_equal(src1.read(), src2.read())


def test_atmos_cli(tmpdir):
    output = str(tmpdir.join("atmosj1.tif"))
    runner = CliRunner()
    result = runner.invoke(
        atmos,
        ["-a", "0.03", "-b", "0.5", "-c", "15", "-j", "1", "tests/rgb8.tif", output],
    )
    assert result.exit_code == 0
    assert os.path.exists(output)

    output2 = str(tmpdir.join("atmosj2.tif"))
    runner = CliRunner()
    result = runner.invoke(
        atmos,
        ["-a", "0.03", "-b", "0.5", "-c", "15", "-j", "2", "tests/rgb8.tif", output2],
    )
    assert result.exit_code == 0
    assert os.path.exists(output2)

    assert equal(output, output2)


def test_color_cli(tmpdir):
    output = str(tmpdir.join("colorj1.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color,
        [
            "-d",
            "uint8",
            "-j",
            "1",
            "tests/rgb8.tif",
            output,
            "gamma 3 1.85",
            "gamma 1,2 1.95",
            "sigmoidal 1,2,3 35 0.13",
            "saturation 1.15",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output)

    output2 = str(tmpdir.join("colorj2.tif"))
    result = runner.invoke(
        color,
        [
            "-d",
            "uint8",
            "-j",
            "2",
            "tests/rgb8.tif",
            output2,
            "gamma 3 1.85",
            "gamma 1,2 1.95",
            "sigmoidal 1,2,3 35 0.13",
            "saturation 1.15",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output2)

    assert equal(output, output2)


def test_bad_op(tmpdir):
    output = str(tmpdir.join("noop.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color, ["-d", "uint8", "-j", "1", "tests/rgb8.tif", output, "foob 115"]
    )
    assert result.exit_code == 2
    assert "foob is not a valid operation" in result.output
    assert not os.path.exists(output)


def test_color_jobsn1(tmpdir):
    output = str(tmpdir.join("colorj1.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color,
        [
            "-d",
            "uint8",
            "-j",
            "-1",
            "tests/rgb8.tif",
            output,
            "gamma 1,2,3 1.85 sigmoidal rgb 35 0.13",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output)


def test_check_jobs():
    assert 1 == check_jobs(1)
    assert check_jobs(-1) > 0
    with pytest.raises(UsageError):
        check_jobs(0)


def test_creation_opts(tmpdir):
    output = str(tmpdir.join("color_opts.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color,
        [
            "--co",
            "compress=jpeg",
            "tests/rgb8.tif",
            output,
            "gamma 1,2,3 1.85 sigmoidal rgb 35 0.13",
        ],
    )
    assert result.exit_code == 0

    with rasterio.open(output, "r") as src:
        assert src.compression == Compression.jpeg

    output = str(tmpdir.join("color_opts.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color, ["--co", "compress=jpeg", "tests/rgb8.tif", output, "gamma 1,2,3 1.85"]
    )
    assert result.exit_code == 0
    with rasterio.open(output, "r") as src:
        assert src.compression == Compression.jpeg

    output = str(tmpdir.join("atmos_opts.tif"))
    runner = CliRunner()
    result = runner.invoke(
        atmos,
        [
            "--co",
            "compress=jpeg",
            "-a",
            "0.03",
            "-b",
            "0.5",
            "-c",
            "15",
            "-j",
            "1",
            "tests/rgb8.tif",
            output,
        ],
    )
    assert result.exit_code == 0
    with rasterio.open(output, "r") as src:
        assert src.compression == Compression.jpeg


def test_color_cli_rgba(tmpdir):
    output = str(tmpdir.join("colorj1.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color,
        [
            "-d",
            "uint8",
            "-j",
            "1",
            "tests/rgba8.tif",
            output,
            "gamma 3 1.85",
            "gamma 1,2 1.95",
            "sigmoidal 1,2,3 35 0.13",
            "saturation 1.15",
        ],
    )
    assert result.exit_code == 0

    with rasterio.open("tests/rgba8.tif") as src:
        with rasterio.open(output) as out:
            assert out.profile["count"] == 4
            # Alpha band is unaltered
            assert np.array_equal(src.read(4), out.read(4))


def test_color_cli_16bit_photointerp(tmpdir):
    output = str(tmpdir.join("color16color.tif"))
    runner = CliRunner()
    result = runner.invoke(
        color,
        [
            "-d",
            "uint16",
            "-j",
            "1",
            "tests/rgb16.tif",
            output,
            "gamma 3 1.85",
            "gamma 1,2 1.95",
        ],
    )
    assert result.exit_code == 0

    with rasterio.open("tests/rgb16.tif") as src:
        with rasterio.open(output) as out:
            assert out.colorinterp == src.colorinterp


def test_color_empty_operations(tmpdir):
    output = str(tmpdir.join("color.tif"))
    runner = CliRunner()
    result = runner.invoke(color, ["tests/rgb8.tif", output])
    assert result.exit_code == 2
    assert not os.path.exists(output)

    result = runner.invoke(color, ["tests/rgb8.tif", output, ", , ,"])
    assert result.exit_code == 2


def test_as_color(tmpdir):
    runner = CliRunner()
    result = runner.invoke(atmos, ["-a", "0.03", "--as-color", "foo.tif", "bar.tif"])
    assert result.exit_code == 0
    assert not os.path.exists("bar.tif")
    assert (
        result.output.strip()
        == "rio color foo.tif bar.tif gamma g 0.99, gamma b 0.97, sigmoidal rgb 10.0 0.15"
    )
