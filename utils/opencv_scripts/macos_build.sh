# https://gist.github.com/liviaerxin/6ee3d4faea1614572e621d81d0e114c8

brew update
brew install cmake gstreamer
pip install numpy

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
    -D OPENCV_EXTRA_MODULES_PATH=../opencv_contrib/modules \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D BUILD_opencv_python2=OFF \
    -D BUILD_opencv_python3=ON \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D CMAKE_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)") \
    -D PYTHON3_EXECUTABLE=$(which python) \
    -D PYTHON3_INCLUDE_DIR=$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
    -D PYTHON3_PACKAGES_PATH=$(python -c "import sysconfig; print(sysconfig.get_path('purelib'))") \
    -D WITH_GSTREAMER=ON \
    -D WITH_OPENGL=ON \
    -D BUILD_EXAMPLES=ON ../opencv

make -j$(sysctl -n hw.physicalcpu)
sudo make install

python -c "import cv2; print(cv2.__version__); print(cv2.getBuildInformation())"
