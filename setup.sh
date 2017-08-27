#!/bin/bash

echo -n "Did you configure the wrapper.ini File? [y/n]"
read answer
if echo "$answer" | grep -iq "^y" ;then
    echo "Good, continuing..."
else
    echo "Start setup.sh after configuring wrapper.ini!"
    exit
fi

DIR=/home/eddy/.local/bin

echo "Installing Security Appliance Wrapper!"
echo "Copy to user binary directory..."
mkdir $DIR/SecAppWrapper
cp -R SecAppWrapper $DIR/SecAppWrapper/
cp startWrapper.py $DIR/SecAppWrapper/
cp wrapper.ini $DIR/SecAppWrapper/
echo "Copy done!"

echo "Installing service..."
sudo cp SAW.service /etc/systemd/user/
sudo touch /var/log/SecAppWrapper.log
sudo chmod 777 /var/log/SecAppWrapper.log

echo "enabling SAW.service!"
systemctl --user enable SAW.service
echo "starting service..."
systemctl --user start SAW.service
echo "succesfully started!"