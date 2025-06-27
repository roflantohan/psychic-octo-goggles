#!/bin/bash

# https://galaktyk.medium.com/how-to-build-opencv-with-gstreamer-b11668fa09c
# https://qengineering.eu/install-opencv-on-raspberry-pi.html

source ./../../.venv/bin/activate

sudo apt-get update
sudo apt-get full-upgrade
sudo apt-get install -y python3-dev python3-numpy python3-pip
sudo apt-get install -y gcc libffi-dev libcairo2 libcairo2-dev libgirepository1.0-dev gobject-introspection meso
sudo apt-get install -y gstreamer1.0*
sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev
sudo apt-get install -y build-essential cmake git unzip pkg-config
sudo apt-get install -y libjpeg-dev libpng-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y libxvidcore-dev libx264-dev
sudo apt-get install -y libtbb-dev libdc1394-22-dev
sudo apt-get install -y libv4l-dev v4l-utils
sudo apt-get install -y libopenblas-dev libatlas-base-dev libblas-dev
sudo apt-get install -y liblapack-dev gfortran libhdf5-dev
sudo apt-get install -y libprotobuf-dev libgoogle-glog-dev libgflags-dev
sudo apt-get install -y protobuf-compiler

pip install numpy==1.26.4

git clone https://github.com/opencv/opencv.git
cd opencv
git checkout master
cd ..

git clone https://github.com/opencv/opencv_contrib.git
cd opencv_contrib
git checkout master
cd ..

mkdir build_opencv
cd build_opencv

cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)") \
    -D OPENCV_EXTRA_MODULES_PATH=../opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D WITH_OPENMP=ON \
    -D WITH_OPENCL=ON \
    -D BUILD_TIFF=ON \
    -D WITH_FFMPEG=ON \
    -D WITH_TBB=ON \
    -D BUILD_TBB=ON \
    -D WITH_GSTREAMER=ON \
    -D BUILD_TESTS=OFF \
    -D WITH_EIGEN=OFF \
    -D WITH_V4L=ON \
    -D WITH_LIBV4L=ON \
    -D WITH_VTK=OFF \
    -D WITH_QT=OFF \
    -D WITH_PROTOBUF=ON \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D OPENCV_FORCE_LIBATOMIC_COMPILER_CHECK=1 \
    -D BUILD_opencv_python2=OFF \
    -D BUILD_opencv_python3=ON \
    -D PYTHON_EXECUTABLE=$(which python) \
    -D PYTHON3_EXECUTABLE=$(which python) \
    -D PYTHON3_INCLUDE_DIR=$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
    -D PYTHON3_PACKAGES_PATH=$(python -c "import sysconfig; print(sysconfig.get_path('purelib'))") \
    -D BUILD_EXAMPLES=ON ../opencv

sudo make -j$(nproc)
sudo make install
sudo ldconfig

python -c "import cv2; print(cv2.__version__); print(cv2.getBuildInformation())"
