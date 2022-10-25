"""Setup script."""

import os
import sys

from setuptools import find_packages, setup
from setuptools.extension import Extension

# Use Cython if available.
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

include_dirs = []
try:
    import numpy

    include_dirs.append(numpy.get_include())
except ImportError:
    print("Numpy and its headers are required to run setup(). Exiting.")
    sys.exit(1)


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
    "click~=8.0",
    "rasterio~=1.0",
]

setup(
    name="rio-color",
    description="Color correction plugin for rasterio",
    long_description=long_description,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="",
    author="Charlie Loyd",
    author_email="charlie@mapbox.com",
    url="https://github.com/mapbox/rio-color",
    license="BSD",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    ext_modules=ext_modules,
    include_dirs=include_dirs,
    extras_require={
        "test": [
            "pytest",
            "colormath==2.0.2",
            "pytest-cov",
        ],
        "mucho": [
            "rio-mucho",
        ],
    },
    entry_points="""
    [rasterio.rio_plugins]
    color=rio_color.scripts.cli:color
    atmos=rio_color.scripts.cli:atmos
    """,
)
