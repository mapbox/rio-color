import os
from codecs import open as codecs_open
from setuptools import setup, find_packages


# Parse the version from the fiona module.
with open('rio_color/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break

# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='rio-color',
      version=version,
      description=u"Color correction plugin for rasterio",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Charlie Loyd",
      author_email='charlie@mapbox.com',
      url='https://github.com/mapbox/rio-color',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=read('requirements.txt').splitlines(),
      extras_require={
          'test': ['pytest', 'pytest-cov', 'codecov', 'raster-tester'],
      },
      entry_points="""
      [rasterio.rio_plugins]
      color=rio_color.scripts.cli:color
      atmos=rio_color.scripts.cli:atmos
      """
      )
