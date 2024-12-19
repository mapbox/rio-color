## Publish to pypi

Following the [general guidelines for publishing](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/), and using Mapbox pypi account credentials, we can make new versions of `rio-color` available on pypi. This approach replaces our previous use of TravisCI and Appveyor, both now deprecated with our organization.

### Build packages

```
python3 -m pip install build twine
python3 -m build --sdist
python3 -m build --wheel
```

### Upload packages
Once you've configured `.pypirc` [with the project token](https://pypi.org/help/#apitoken), you can upload the packages to pypi.

```
twine upload dist/* --repository rio-color
```

And confirm the upload at [the project page](https://pypi.org/project/rio-color/#history).