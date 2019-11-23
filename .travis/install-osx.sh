#!/bin/sh

set -ex # reduced logging
#set -e

brew update # this seems to help to work around some homebrew issues; and fails on others

# Python 3.6.5_1 is installed by default
# for Python 3.7:
# avoid issues with brew auto updates by deactivating them
#   
brew upgrade python
#HOMEBREW_NO_AUTO_UPDATE=1 brew install python

# following https://stackoverflow.com/questions/51125013/how-can-i-install-a-previous-version-of-python-3-in-macos-using-homebrew/51125014#51125014
# to install Python 3.6.5
#brew remove --ignore-dependencies python 1>/dev/null 2>&1
#brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb 1>/dev/null 2>&1

# to work around a wget open ssl issue: dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
# however for now we settled to use curl instead to download the upload script
#brew uninstall wget
#brew install wget


brew install p7zip

pip3 install --upgrade pip
# to allow the installation of numpy >v1.15.4, avoiding the Permission denied: '/usr/local/bin/f2py' error, we run the following pip3 installs under sudo:
# (an alternative could be to use pip install --user ..)
sudo pip3 install -r src/requirements.txt
sudo pip3 install -r src/requirements-${TRAVIS_OS_NAME}.txt
sudo rm -rf /usr/local/lib/python3.6/site-packages/matplotlib/mpl-data/sample_data

#.travis/install-phidgets.sh
.travis/install-snap7.sh
