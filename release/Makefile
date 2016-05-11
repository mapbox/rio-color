# From https://github.com/sgillies/frs-wheel-builds
# Copyright (c) 2015, Sean Gillies
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of frs-wheel-builds nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

SHELL = /bin/bash

MACOSX_DEPLOYMENT_TARGET = 10.6
CFLAGS = -arch i386 -arch x86_64
CXXFLAGS = -arch i386 -arch x86_64
GEOS_CONFIG = "geos-config"
GDAL_CONFIG = "gdal-config"
PYFRAMEWORK = "/Library/Frameworks/Python.framework/Versions"

all: build

build: rio_color_27 rio_color_34 rio_color_35

venv27:
	virtualenv -p $(PYFRAMEWORK)/2.7/bin/python2.7 venv27 && \
	source venv27/bin/activate && \
	pip install -U pip && \
	pip install -U wheel delocate && \
	pip install numpy

venv34:
	virtualenv -p $(PYFRAMEWORK)/3.4/bin/python3.4 venv34 && \
	source venv34/bin/activate && \
	pip install -U pip && \
	pip install -U wheel delocate && \
	pip install numpy

venv35:
	virtualenv -p $(PYFRAMEWORK)/3.5/bin/python3.5 venv35 && \
	source venv35/bin/activate && \
	pip install -U pip && \
	pip install -U wheel delocate && \
	pip install numpy

rio_color_27: venv27
	source venv27/bin/activate && \
	cd .. && \
	pip install -r requirements-dev.txt && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" pip install -e . && \
	py.test tests && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" python setup.py sdist bdist_wheel

rio_color_34: venv34
	source venv34/bin/activate && \
	cd .. && \
	pip install -r requirements-dev.txt && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" pip install -e . && \
	py.test tests && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" python setup.py sdist bdist_wheel

rio_color_35: venv35
	source venv35/bin/activate && \
	cd .. && \
	pip install -r requirements-dev.txt && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" pip install -e . && \
	py.test tests && \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) PACKAGE_DATA=1 CXXFLAGS="$(CXXFLAGS)" CFLAGS="$(CFLAGS) $$($(GDAL_CONFIG) --cflags)" LDFLAGS="$$($(GDAL_CONFIG) --libs) $(CFLAGS)" python setup.py sdist bdist_wheel


publish: build
	ls ../dist
	twine upload ../dist/*

clean:
	rm -rf ../dist
	rm -rf venv27
	rm -rf venv34
	rm -rf venv35
