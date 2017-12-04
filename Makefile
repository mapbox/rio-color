SHELL = /bin/bash

all: build

build: sdist osx-wheels manylinux-wheels

image:
	docker build -f Dockerfile.wheels -t rio-wheelbuilder .

osx-wheels:
	build-macosx-wheels.sh

manylinux-wheels: image
	docker run -v $(CURDIR):/src rio-wheelbuilder bash -c "/src/build-linux-wheels.sh"

sdist:
	python setup.py sdist

clean:
	rm -rf dist
	rm -rf venv*
