"""Setup script."""

import os
import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension

# Use Cython if available.
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None


def get_numpy_include():
    """Helper function to find the numpy include path

    The purpose of this function is to postpone importing numpy
    until it is actually installed, so that the get_include()
    method can be invoked.
    """
    import numpy
    yield numpy.get_include()


include_dirs = [
    get_numpy_include()
]

# Parse the version from the fiona module.
with open("rio_color/__init__.py") as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break

long_description = """Color adjustment plugin for rasterio.

See https://github.com/mapbox/rio-color for docs."""


def read(fname):
    """Read a file's contents."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


if cythonize and "clean" not in sys.argv:
    ext_modules = cythonize(
        [
            Extension(
                "rio_color.colorspace",
                ["rio_color/colorspace.pyx"],
                extra_compile_args=["-O2"],
            )
        ]
    )
else:
    ext_modules = [Extension("rio_color.colorspace", ["rio_color/colorspace.c"])]

inst_reqs = [
    "click>=4.0,<8",
    "rasterio>=1.0a11",
    "rio-mucho",
    "enum34 ; python_version < '3.4'",
]

setup(
    name="rio-color",
    version=version,
    description=u"Color correction plugin for rasterio",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="",
    author=u"Charlie Loyd",
    author_email="charlie@mapbox.com",
    url="https://github.com/mapbox/rio-color",
    license="BSD",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    ext_modules=ext_modules,
    include_dirs=include_dirs,
    extras_require={"test": ["pytest", "colormath==2.0.2", "pytest-cov", "codecov"]},
    setup_requires=["numpy"],
    entry_points="""
    [rasterio.rio_plugins]
    color=rio_color.scripts.cli:color
    atmos=rio_color.scripts.cli:atmos
    """,
)
