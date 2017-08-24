#!/bin/bash

echo "Installing Security Appliance Wrapper!"
echo "Copy to user binary directory..."
mkdir /usr/local/bin/SecAppWrapper
cp SecAppWrapper /usr/local/bin/SecAppWrapper/
cp startWrapper.py /usr/local/bin/SecAppWrapper/
cp .argconf /usr/local/bin/SecAppWrapper

echo "Copy done!"

echo "Installing service..."
cp SAW.service /etc/systemd/system/