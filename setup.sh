#!/bin/bash

DIR=/home/eddy/.local/bin/

echo "Installing Security Appliance Wrapper!"
echo "Copy to user binary directory..."
mkdir $DIR/SecAppWrapper
cp SecAppWrapper $DIR/SecAppWrapper/
cp startWrapper.py $DIR/SecAppWrapper/
cp wrapper.ini $DIR/SecAppWrapper/
echo "Copy done!"

echo "Installing service..."
cp SAW.service /etc/systemd/user/

echo "enabling SAW.service!"
systemctl --user enable SAW.service
echo "starting service..."
systemctl --user start SAW.service
echo "succesfully started!"