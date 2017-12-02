#!/bin/bash
set -eu

UNREPAIRED_WHEELS=/tmp/wheels
export CFLAGS="-I/usr/local/ssl/include"
export LDFLAGS="-L/usr/local/ssl/lib"
export PACKAGE_DATA=1

cd /src

function clean {
    find "." -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print
}

for version in cp27-cp27m cp27-cp27mu cp34-cp34m cp35-cp35m cp36-cp36m; do
    bin=/opt/python/${version}/bin
    clean
    $bin/pip install -r requirements-dev.txt
    $bin/pip install .
    $bin/pytest -v
    $bin/python setup.py bdist_wheel --dist-dir ${UNREPAIRED_WHEELS}
    auditwheel repair $(ls ${UNREPAIRED_WHEELS}/*${version}*.whl) -w /src/dist
    clean
done
