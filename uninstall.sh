#!/bin/bash

echo -n "Are you sure you want to uninstall? [y/n]"
read answer
if echo "$answer" | grep -iq "^y" ;then
    echo "Good, continuing..."
else
    echo "OK."
    exit
fi

DIR=/home/eddy/.local/bin

systemctl --user stop SAW.service
systemctl --user disable SAW.service
sudo rm /var/log/SecAppWrapper.log
sudo rm /etc/systemd/user/SAW.service
rm -rf $DIR/SecAppWrapper

echo "reset done."