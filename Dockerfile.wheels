FROM quay.io/pypa/manylinux1_x86_64

# See frs-wheel-builds
RUN sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf \
    && sed -i 's/mirrorlist/#mirrorlist/' /etc/yum.repos.d/CentOS-Base.repo \
    && sed -i 's|#baseurl=http://mirror.centos.org/centos/$releasever|baseurl=http://vault.centos.org/5.11|' /etc/yum.repos.d/CentOS-Base.repo \
    && sed -i 's/^/#/' /etc/yum.repos.d/libselinux.repo
RUN yum update -y && yum install -y json-c-devel zlib-devel expat-devel

# Install rasterio + deps
RUN /opt/python/cp27-cp27m/bin/pip install --pre "rasterio>=1.0a11" --only-binary rasterio
RUN /opt/python/cp27-cp27mu/bin/pip install --pre "rasterio>=1.0a11" --only-binary rasterio
RUN /opt/python/cp34-cp34m/bin/pip install --pre "rasterio>=1.0a11" --only-binary rasterio
RUN /opt/python/cp35-cp35m/bin/pip install --pre "rasterio>=1.0a11" --only-binary rasterio
RUN /opt/python/cp36-cp36m/bin/pip install --pre "rasterio>=1.0a11" --only-binary rasterio

COPY requirements-dev.txt /requirements-dev.txt
RUN /opt/python/cp27-cp27m/bin/pip install -r /requirements-dev.txt
RUN /opt/python/cp27-cp27mu/bin/pip install -r /requirements-dev.txt
RUN /opt/python/cp34-cp34m/bin/pip install -r /requirements-dev.txt
RUN /opt/python/cp35-cp35m/bin/pip install -r /requirements-dev.txt
RUN /opt/python/cp36-cp36m/bin/pip install -r /requirements-dev.txt

WORKDIR /src
CMD ["/src/build-linux-wheels.sh"]
