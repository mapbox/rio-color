#!/bin/bash
set -u

PYFRAMEWORK="/Library/Frameworks/Python.framework/Versions"

export MACOSX_DEPLOYMENT_TARGET=10.6
export CFLAGS="-arch i386 -arch x86_64"
export CXXFLAGS="-arch i386 -arch x86_64"
export LDFLAGS="$CFLAGS"
export PS1='$'

function clean {
    find "." -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print
}

for version in "2.7" "3.4" "3.5" "3.6"; do
    clean
    virtualenv -p ${PYFRAMEWORK}/${version}/bin/python${version} venv${version}
    source venv${version}/bin/activate
    pip install -U pip
    pip install -U wheel delocate
	pip install -r requirements-dev.txt
	pip install -r requirements.txt
    python setup.py bdist_wheel
    py.test tests
    clean
done
