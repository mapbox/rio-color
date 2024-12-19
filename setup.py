"""Setup script."""

import os
import sys
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import numpy as np

include_dirs = []
try:
    include_dirs.append(np.get_include())
except ImportError:
    print("Numpy and its headers are required to run setup(). Exiting.")
    sys.exit(1)


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


extensions = [
    Extension(
        "rio_color.colorspace",
        ["rio_color/colorspace.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_2_0_API_VERSION")],
    )
]

inst_reqs = ["click>=8.0", "rasterio~=1.4", "rio-mucho"]

setup(
    name="rio-color",
    version=version,
    description="Color correction plugin for rasterio",
    long_description=long_description,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
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
    ext_modules=cythonize(extensions),
    include_dirs=include_dirs,
    extras_require={"test": ["pytest", "colormath==3.0.0", "pytest-cov", "codecov"]},
    entry_points="""
    [rasterio.rio_plugins]
    color=rio_color.scripts.cli:color
    atmos=rio_color.scripts.cli:atmos
    """,
)
